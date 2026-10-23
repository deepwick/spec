import itertools
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from deepwick_spec.ansi import plain

_counter = itertools.count()


def tmux_available() -> bool:
    return shutil.which("tmux") is not None


def _snapshot(base: list[str]) -> str:
    return subprocess.run([*base, "capture-pane", "-e", "-p", "-t", "0"], capture_output=True, text=True).stdout


def _alive(base: list[str]) -> bool:
    return subprocess.run([*base, "has-session"], capture_output=True).returncode == 0


def _wait(base: list[str], wait_for: str | None, timeout: float, settle: float, changed_from: str | None = None) -> str:
    deadline = time.monotonic() + timeout
    previous = None
    current = ""
    matched = False
    while time.monotonic() < deadline:
        time.sleep(settle)
        if not _alive(base):
            raise TimeoutError(f"app exited before the pane was ready; last pane text:\n{plain(current)}")
        current = _snapshot(base)
        if wait_for is not None and not matched:
            matched = wait_for in plain(current)
        ready = matched if wait_for is not None else bool(current.strip())
        if changed_from is not None and current == changed_from:
            ready = False
        if ready and current == previous:
            return current
        previous = current
    target = f"for {wait_for!r}" if wait_for else "for the pane to settle"
    raise TimeoutError(f"timed out waiting {target}; pane text:\n{plain(current)}")


def _kill_pane(base: list[str]) -> None:
    # kill-server hangs up the pane, and apps that handle SIGHUP (xonsh) then write to the dead
    # pty, crash on EIO and trigger desktop crash reporters. SIGKILL runs no handlers.
    shown = subprocess.run([*base, "display-message", "-p", "-t", "0", "#{pane_pid}"], capture_output=True, text=True)
    if shown.returncode != 0 or not shown.stdout.strip().isdigit():
        return
    try:
        os.killpg(int(shown.stdout.strip()), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def capture(
    command: str,
    env: dict | None = None,
    *,
    size: tuple[int, int] = (100, 30),
    wait_for: str | None = None,
    literal: str | None = None,
    keys: tuple[str, ...] = (),
    after: str | None = None,
    timeout: float = 15.0,
    settle: float = 0.4,
    background: str | None = None,
) -> str:
    socket = f"deepwick-test-{os.getpid()}-{next(_counter)}"
    base = ["tmux", "-L", socket, "-f", "/dev/null"]
    # A detached tmux has no client to answer background queries (OSC 11); a pane background
    # lets tmux answer them itself, for apps that pick dark/light themes from the reply.
    conf = None
    if background:
        conf = tempfile.NamedTemporaryFile("w", prefix="deepwick-tmux-", suffix=".conf", delete=False)
        conf.write(f'set -g window-style "bg={background}"\n')
        conf.close()
    start = ["tmux", "-L", socket, "-f", conf.name] if conf else base
    env_args: list[str] = []
    for key, value in {"COLORTERM": "truecolor", **(env or {})}.items():
        env_args += ["-e", f"{key}={value}"]
    started = subprocess.run(
        [*start, "new-session", "-d", "-P", "-F", "#{socket_path}", "-x", str(size[0]), "-y", str(size[1]), *env_args, command],
        capture_output=True, text=True,
    )
    if conf:
        os.unlink(conf.name)
    if started.returncode != 0:
        subprocess.run([*base, "kill-server"], capture_output=True)
        default_dir = Path(os.environ.get("TMUX_TMPDIR") or "/tmp") / f"tmux-{os.getuid()}"
        (default_dir / socket).unlink(missing_ok=True)
        raise RuntimeError(f"tmux new-session failed: {started.stderr.strip()}")
    socket_path = started.stdout.strip()
    try:
        text = _wait(base, wait_for, timeout, settle)
        if literal is None and not keys:
            return text
        if literal is not None:
            subprocess.run([*base, "send-keys", "-t", "0", "-l", literal], check=True)
        for key in keys:
            subprocess.run([*base, "send-keys", "-t", "0", key], check=True)
        return _wait(base, after, timeout, settle, changed_from=None if after else text)
    finally:
        _kill_pane(base)
        subprocess.run([*base, "kill-server"], capture_output=True)
        # tmux never unlinks its socket on exit, and unique names mean nothing reuses it.
        if socket_path:
            Path(socket_path).unlink(missing_ok=True)
