import itertools
import os
import shutil
import subprocess
import time

from deepwick_spec.ansi import plain

_counter = itertools.count()


def tmux_available() -> bool:
    return shutil.which("tmux") is not None


def _snapshot(base: list[str]) -> str:
    return subprocess.run([*base, "capture-pane", "-e", "-p", "-t", "0"], capture_output=True, text=True).stdout


def _wait(base: list[str], wait_for: str | None, timeout: float, settle: float) -> str:
    deadline = time.monotonic() + timeout
    previous = None
    current = ""
    while time.monotonic() < deadline:
        time.sleep(settle)
        current = _snapshot(base)
        if wait_for is not None:
            if wait_for in plain(current):
                time.sleep(settle)
                return _snapshot(base)
        elif current.strip() and current == previous:
            return current
        previous = current
    target = f"for {wait_for!r}" if wait_for else "for the pane to settle"
    raise TimeoutError(f"timed out waiting {target}; pane text:\n{plain(current)}")


def capture(
    command: str,
    env: dict | None = None,
    *,
    size: tuple[int, int] = (100, 30),
    wait_for: str | None = None,
    literal: str | None = None,
    keys: tuple[str, ...] = (),
    timeout: float = 15.0,
    settle: float = 0.4,
) -> str:
    socket = f"deepwick-test-{os.getpid()}-{next(_counter)}"
    base = ["tmux", "-L", socket, "-f", "/dev/null"]
    env_args: list[str] = []
    for key, value in {"COLORTERM": "truecolor", **(env or {})}.items():
        env_args += ["-e", f"{key}={value}"]
    subprocess.run([*base, "new-session", "-d", "-x", str(size[0]), "-y", str(size[1]), *env_args, command], check=True)
    try:
        text = _wait(base, wait_for, timeout, settle)
        if literal is None and not keys:
            return text
        if literal is not None:
            subprocess.run([*base, "send-keys", "-t", "0", "-l", literal], check=True)
        for key in keys:
            subprocess.run([*base, "send-keys", "-t", "0", key], check=True)
        return _wait(base, None, timeout, settle)
    finally:
        subprocess.run([*base, "kill-server"], capture_output=True)
