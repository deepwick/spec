import shutil
from pathlib import Path

import pytest

from deepwick_spec.check_port import CREDIT, _check_workflow, _flatten, check_port, main
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


def test_flatten_handles_bare_quote_lines():
    assert _flatten("> a\n>\n> b") == "a b"


def test_spec_ref_must_match_workflow_ref(tmp_path):
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "check.yml").write_text(
        "jobs:\n  port:\n    uses: deepwick/spec/.github/workflows/check.yml@v1\n    with:\n      spec-ref: main\n"
    )
    assert any("spec-ref" in p for p in _check_workflow(tmp_path))
    (wf / "check.yml").write_text("jobs:\n  port:\n    uses: deepwick/spec/.github/workflows/check.yml@main\n")
    assert _check_workflow(tmp_path) == []


CALL = "deepwick/spec/.github/workflows/check.yml@"


def workflow(tmp_path, text):
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True, exist_ok=True)
    (wf / "check.yml").write_text(text)
    return _check_workflow(tmp_path)


def test_workflow_ignores_commented_uses(tmp_path):
    text = f"jobs:\n  port:\n    # uses: {CALL}v9\n    uses: {CALL}main  # pinned later\n"
    assert workflow(tmp_path, text) == []


def test_workflow_comment_only_call_is_missing(tmp_path):
    assert any("does not call" in p for p in workflow(tmp_path, f"jobs:\n  port:\n    # uses: {CALL}main\n"))


def test_workflow_checks_every_calling_job(tmp_path):
    text = (
        f"jobs:\n  a:\n    uses: {CALL}main\n"
        f"  b:\n    uses: {CALL}v1\n    with:\n      spec-ref: main\n"
    )
    problems = workflow(tmp_path, text)
    assert len(problems) == 1 and "@v1" in problems[0]


def test_workflow_flow_style_spec_ref(tmp_path):
    assert workflow(tmp_path, f"jobs:\n  port:\n    uses: {CALL}v1\n    with: {{ spec-ref: v1 }}\n") == []
    assert workflow(tmp_path, f"jobs:\n  port:\n    uses: {CALL}v1\n    with: {{spec-ref: 'main'}}\n") != []


def test_workflow_empty_spec_ref(tmp_path):
    problems = workflow(tmp_path, f"jobs:\n  port:\n    uses: {CALL}main\n    with:\n      spec-ref:\n")
    assert any("empty" in p for p in problems)
    assert any("empty" in p for p in workflow(tmp_path, f'jobs:\n  port:\n    uses: {CALL}main\n    with:\n      spec-ref: ""\n'))


def test_workflow_expression_spec_ref(tmp_path):
    text = f"jobs:\n  port:\n    uses: {CALL}main\n    with:\n      spec-ref: ${{{{ github.ref_name }}}}\n"
    assert any("expression" in p for p in workflow(tmp_path, text))
