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
    text = (REPO / "README.md").read_text(encoding="utf-8").replace("> ", " ")
    assert CREDIT in " ".join(text.split())


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


def test_check_workflow_is_reusable_and_runs_check_palette():
    text = (REPO / ".github" / "workflows" / "check.yml").read_text(encoding="utf-8")
    assert "workflow_call" in text
    assert "check-palette ." in text
