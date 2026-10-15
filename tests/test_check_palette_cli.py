import os

import pytest

from deepwick_spec.check_palette import Violation, main, scan
from deepwick_spec.palette import load_palette

ALLOWED = load_palette().allowed_hex()


@pytest.fixture
def port(tmp_path):
    root = tmp_path / "port"
    root.mkdir()
    return root


def test_clean_port_exits_0(port, capsys):
    (port / "theme.conf").write_text("background=#04041a\nforeground=#D4D4D4\ncomment=#7a86a8cc\n")
    assert main([str(port)]) == 0
    assert "0 violation(s) in 1 file(s)" in capsys.readouterr().err


def test_violation_reported_with_location(port, capsys):
    (port / "theme.conf").write_text("ok=#04041a\nbad = #123456\n")
    assert main([str(port)]) == 1
    assert capsys.readouterr().out.strip() == "theme.conf:2:7: #123456 not in Deepwick palette"


def test_violation_str_format():
    assert str(Violation("a/b.lua", 3, 9, "#ABCDEF")) == "a/b.lua:3:9: #ABCDEF not in Deepwick palette"


def test_nested_paths_are_relative_posix(port):
    (port / "lua" / "deepwick").mkdir(parents=True)
    (port / "lua" / "deepwick" / "colors.lua").write_text('red = "#CD3131"\n')
    violations, checked = scan(port, ALLOWED)
    assert checked == 1
    assert violations == [Violation("lua/deepwick/colors.lua", 1, 8, "#CD3131")]


def test_allow_file_permits_extra_colors(port):
    (port / ".palette-allow").write_text("# konsole needs pure black\n#000000\n")
    (port / "Deepwick.colorscheme").write_text("Color=0,0,0\nhex=#000000\n")
    violations, checked = scan(port, ALLOWED)
    assert violations == []
    assert checked == 1  # the allow file itself is not scanned


def test_ignore_file_skips_paths(port):
    (port / ".palette-ignore").write_text("vendor/\n")
    (port / "vendor").mkdir()
    (port / "vendor" / "lib.css").write_text("a{color:#123456}\n")
    (port / "theme.css").write_text("a{color:#569CD6}\n")
    violations, checked = scan(port, ALLOWED)
    assert violations == []
    assert checked == 1


def test_git_directory_is_skipped(port):
    (port / ".git").mkdir()
    (port / ".git" / "config").write_text("color = #123456\n")
    assert scan(port, ALLOWED) == ([], 0)


def test_binary_files_are_skipped(port):
    (port / "screenshot.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00#123456")
    assert scan(port, ALLOWED) == ([], 0)


def test_non_utf8_text_is_scanned_without_crashing(port):
    (port / "legacy.conf").write_bytes("name=Caf\xe9\ncolor=#123456\n".encode("latin-1"))
    violations, checked = scan(port, ALLOWED)
    assert checked == 1
    assert [v.raw for v in violations] == ["#123456"]


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read everything")
def test_unreadable_file_warns_and_continues(port, capsys):
    secret = port / "secret.conf"
    secret.write_text("#123456\n")
    secret.chmod(0)
    (port / "theme.conf").write_text("#123456\n")
    try:
        violations, checked = scan(port, ALLOWED)
    finally:
        secret.chmod(0o600)
    assert checked == 1
    assert [v.path for v in violations] == ["theme.conf"]
    assert "secret.conf" in capsys.readouterr().err


def test_single_file_path(port, capsys):
    target = port / "deepwick.toml"
    target.write_text('fg = "#D4D4D4"\nbad = "#010101"\n')
    assert main([str(target)]) == 1
    assert capsys.readouterr().out.strip() == f"{target}:2:8: #010101 not in Deepwick palette"


def test_missing_path_exits_2(tmp_path, capsys):
    assert main([str(tmp_path / "nosuchdir")]) == 2
    assert "no such file or directory" in capsys.readouterr().err


def test_invalid_palette_exits_2(port, palette_data, write_palette, capsys):
    palette_data["ansi"].pop("brightRed")
    assert main([str(port), "--palette", str(write_palette(palette_data))]) == 2
    assert "invalid palette" in capsys.readouterr().err


def test_default_path_is_cwd(port, monkeypatch):
    (port / "theme.conf").write_text("#123456\n")
    monkeypatch.chdir(port)
    assert main([]) == 1






def test_fifo_path_is_an_error(tmp_path, capsys):
    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)
    assert main([str(fifo)]) == 2
    assert "not a regular file or directory" in capsys.readouterr().err


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read anything")
def test_unreadable_dir_is_an_error(tmp_path, capsys):
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0)
    try:
        assert main([str(locked)]) == 2
        assert "cannot read" in capsys.readouterr().err
    finally:
        locked.chmod(0o755)


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read anything")
def test_unreadable_subdir_warns(tmp_path, capsys):
    (tmp_path / "ok.css").write_text("a {}\n")
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0)
    try:
        assert main([str(tmp_path)]) == 0
        assert "cannot read" in capsys.readouterr().err
    finally:
        locked.chmod(0o755)
