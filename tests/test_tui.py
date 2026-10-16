import os
from pathlib import Path

import pytest

from deepwick_spec.ansi import style_of
from deepwick_spec.tui import capture, tmux_available

pytestmark = pytest.mark.skipif(not tmux_available(), reason="requires tmux")


def test_capture_sees_truecolor_output():
    text = capture(r"printf '\033[38;2;86;156;214mblue\033[0m\n'; sleep 30", wait_for="blue")
    assert style_of(text, "blue")["fg"] == "#569cd6"


def test_capture_passes_environment():
    text = capture('printf "%s\\n" "$DEEPWICK_PROBE $COLORTERM"; sleep 30', {"DEEPWICK_PROBE": "probe-ok"}, wait_for="probe-ok")
    assert "probe-ok truecolor" in text


def test_capture_types_literal_text_and_keys():
    text = capture("printf 'ready\\n'; cat", wait_for="ready", literal="hello deepwick", keys=("Enter",))
    assert text.count("hello deepwick") == 2


def test_capture_times_out_with_pane_text():
    with pytest.raises(TimeoutError, match="still waiting"):
        capture("printf 'still waiting\\n'; sleep 30", wait_for="never shown", timeout=1.5)


def test_capture_waits_for_text_after_keys():
    text = capture("sh -c 'echo ready; read x; sleep 1; echo got-$x; sleep 30'", wait_for="ready", literal="abc", keys=("Enter",), after="got-abc")
    assert "got-abc" in text


def test_capture_reports_dead_app_quickly():
    import time

    start = time.monotonic()
    with pytest.raises(TimeoutError, match="exited"):
        capture("true", wait_for="never", timeout=10)
    assert time.monotonic() - start < 5


def _own_sockets():
    root = Path(os.environ.get("TMUX_TMPDIR") or "/tmp") / f"tmux-{os.getuid()}"
    return set(root.glob(f"deepwick-test-{os.getpid()}-*"))


def test_capture_removes_socket_file():
    before = _own_sockets()
    capture("printf 'x\\n'; sleep 30", wait_for="x")
    assert _own_sockets() == before


def test_capture_removes_socket_file_when_app_exits_early():
    before = _own_sockets()
    with pytest.raises(TimeoutError, match="exited"):
        capture("true", wait_for="never", timeout=10)
    assert _own_sockets() == before


@pytest.mark.skipif(not tmux_available(), reason="requires tmux")
@pytest.mark.parametrize("tmpdir", [None, ""])
def test_capture_reports_tmux_errors(tmpdir, monkeypatch):
    if tmpdir is None:
        monkeypatch.delenv("TMUX_TMPDIR", raising=False)
    else:
        monkeypatch.setenv("TMUX_TMPDIR", tmpdir)
    sockets = Path("/tmp") / f"tmux-{os.getuid()}"
    before = set(sockets.glob(f"deepwick-test-{os.getpid()}-*"))
    with pytest.raises(RuntimeError, match="width too small|size"):
        capture("true", size=(0, 0))
    assert set(sockets.glob(f"deepwick-test-{os.getpid()}-*")) == before, "failed new-session left its socket"
