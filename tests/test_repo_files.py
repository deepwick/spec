import re
import shutil
import subprocess
from pathlib import Path

import pytest

from deepwick_spec.palette import load_palette

REPO = Path(__file__).resolve().parents[1]
CREDIT = (
    "Deepwick is an unofficial theme derived from [Polywick Blue](https://vscode.polywickstudio.net) "
    "by Polywick Studio (MIT). Not affiliated with Polywick Studio."
)


def test_readme_has_credit_line():
    from deepwick_spec.check_port import _flatten
    assert CREDIT in _flatten((REPO / "README.md").read_text(encoding="utf-8"))


def test_readme_lists_every_palette_color():
    readme = (REPO / "README.md").read_text(encoding="utf-8").lower()
    palette = load_palette()
    for hex_ in [*palette.colors.values(), *palette.ansi.values()]:
        assert hex_.lower() in readme, hex_


def test_license_preserves_polywick_notice():
    text = (REPO / "LICENSE").read_text(encoding="utf-8")
    assert "Copyright (c) 2026 Polywick Studio" in text
    assert "Copyright (c) 2026 Deepwick contributors" in text
    assert "MIT License" in text


@pytest.mark.skipif(shutil.which("uv") is None, reason="requires uv")
@pytest.mark.parametrize("name", ["ci.yml", "check.yml"])
def test_workflows_are_valid_yaml(name):
    path = REPO / ".github" / "workflows" / name
    subprocess.run(
        ["uv", "run", "--no-project", "--with", "pyyaml", "python", "-c",
         "import sys, yaml; yaml.safe_load(open(sys.argv[1]))", str(path)],
        check=True, capture_output=True,
    )


def test_check_workflow_is_reusable_and_runs_check_port():
    text = (REPO / ".github" / "workflows" / "check.yml").read_text(encoding="utf-8")
    assert "workflow_call" in text
    assert "check-port ." in text
    assert re.search(r"^name: check-port$", text, re.M)
    assert re.search(r"^jobs:\n  check-port:$", text, re.M)


SPEC_SCOPES = [
    "punctuation.definition.comment", "string.quoted.docstring", "keyword.other.documentation",
    "keyword.operator.expression", "keyword.operator.cast", "keyword.operator.sizeof", "keyword.control.from",
    "entity.name.namespace", "support.type", "meta.function-call", "support.function.magic",
    "entity.name.function.decorator", "punctuation.definition.string", "string.quoted.include",
    "punctuation.definition.string.begin.include", "keyword.preprocessor", "cls",
    "support.type.property-name", "support.constant.property-value", "entity.other.attribute-name.class.css",
    "punctuation.definition.group.regexp", "entity.other.attribute-name", "variable.other.object.property",
]


def test_readme_syntax_table_lists_every_spec_scope():
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    missing = [scope for scope in SPEC_SCOPES if scope not in readme]
    assert missing == []


def _display(name: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r" \1", name).title()


def test_readme_files_table_matches_palette():
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    palette = load_palette()
    for role, style in palette.files.items():
        row = f"| `{role}` | {_display(style.color)} | {' '.join(style.style)} |"
        assert row.replace("|  |", "| |") in readme.replace("|  |", "| |"), row
