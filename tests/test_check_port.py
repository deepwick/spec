import shutil
from pathlib import Path

import pytest

from deepwick_spec.check_port import CREDIT, check_port, main
from deepwick_spec.palette import load_palette

REPO = Path(__file__).resolve().parents[1]
ALLOWED = load_palette().allowed_hex()
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


@pytest.fixture
def port(tmp_path):
    root = tmp_path / "port"
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / "README.md").write_text(f"# Deepwick for Thing\n\n> {CREDIT}\n\nTested with Thing 1.2.3.\n")
    shutil.copy(REPO / "LICENSE", root / "LICENSE")
    (root / ".github" / "workflows" / "check.yml").write_text(
        "jobs:\n  port:\n    uses: deepwick/spec/.github/workflows/check.yml@main\n"
    )
    (root / "screenshot.png").write_bytes(PNG)
    (root / "theme.conf").write_text("bg=#04041a\n")
    return root


def test_clean_port_has_no_problems(port):
    assert check_port(port, ALLOWED) == []


def test_credit_line_may_wrap_across_blockquote_lines(port):
    wrapped = CREDIT.replace(" by Polywick", "\n> by Polywick")
    (port / "README.md").write_text(f"> {wrapped}\n\nTested with Thing 1.2.\n")
    assert check_port(port, ALLOWED) == []


@pytest.mark.parametrize(
    ("mutate", "problem"),
    [
        (lambda p: (p / "README.md").unlink(), "README.md is missing"),
        (lambda p: (p / "README.md").write_text("Tested with Thing 1.2.\n"), "credit line"),
        (lambda p: (p / "README.md").write_text(f"> {CREDIT}\n"), "Tested with"),
        (lambda p: (p / "LICENSE").unlink(), "LICENSE is missing"),
        (lambda p: (p / "LICENSE").write_text("MIT License\nCopyright (c) 2026 Someone\n"), "Polywick Studio"),
        (lambda p: (p / ".github" / "workflows" / "check.yml").unlink(), "check.yml is missing"),
        (lambda p: (p / ".github" / "workflows" / "check.yml").write_text("jobs: {}\n"), "reusable workflow"),
        (lambda p: (p / "screenshot.png").unlink(), "screenshot.png is missing"),
        (lambda p: (p / "screenshot.png").write_bytes(b"GIF89a"), "not a PNG"),
        (lambda p: (p / "theme.conf").write_text("bg=#123456\n"), "theme.conf:1:4: #123456 not in Deepwick palette"),
    ],
)
def test_each_problem_is_reported(port, mutate, problem):
    mutate(port)
    problems = check_port(port, ALLOWED)
    assert any(problem in p for p in problems), problems


def test_main_clean_exits_0(port, capsys):
    assert main([str(port)]) == 0
    assert "0 problem(s)" in capsys.readouterr().err


def test_main_problems_exit_1(port, capsys):
    (port / "screenshot.png").unlink()
    assert main([str(port)]) == 1
    assert "screenshot.png is missing" in capsys.readouterr().out


def test_main_missing_path_exits_2(tmp_path, capsys):
    assert main([str(tmp_path / "nope")]) == 2
    assert "not a directory" in capsys.readouterr().err


def test_main_file_path_exits_2(port, capsys):
    assert main([str(port / "README.md")]) == 2


def test_main_invalid_palette_exits_2(port, palette_data, write_palette, capsys):
    palette_data["colors"]["red"] = "#nothex"
    assert main([str(port), "--palette", str(write_palette(palette_data))]) == 2
    assert "invalid palette" in capsys.readouterr().err
