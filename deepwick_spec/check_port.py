import argparse
import re
import sys
from pathlib import Path

from deepwick_spec.check_palette import scan
from deepwick_spec.palette import PaletteError, load_palette

CREDIT = (
    "Deepwick is an unofficial theme derived from [Polywick Blue](https://vscode.polywickstudio.net) "
    "by Polywick Studio (MIT). Not affiliated with Polywick Studio."
)
WORKFLOW_REF = "deepwick/spec/.github/workflows/check.yml@"
_TESTED = re.compile(r"Tested with \S.* \d+(\.\d+)*")


def _flatten(markdown: str) -> str:
    return " ".join(markdown.replace("> ", " ").split())


def _check_readme(root: Path) -> list[str]:
    path = root / "README.md"
    if not path.is_file():
        return ["README.md is missing"]
    text = _flatten(path.read_text(encoding="utf-8", errors="replace"))
    problems = []
    if CREDIT not in text:
        problems.append("README.md lacks the Deepwick credit line")
    if not _TESTED.search(text):
        problems.append("README.md lacks a 'Tested with <app> <version>' line")
    return problems


def _check_license(root: Path) -> list[str]:
    path = root / "LICENSE"
    if not path.is_file():
        return ["LICENSE is missing"]
    text = path.read_text(encoding="utf-8", errors="replace")
    if "MIT License" not in text or "Copyright (c) 2026 Polywick Studio" not in text:
        return ["LICENSE must be the MIT text with Polywick Studio's copyright notice (copy spec/LICENSE)"]
    return []


def _check_workflow(root: Path) -> list[str]:
    path = root / ".github" / "workflows" / "check.yml"
    if not path.is_file():
        return [".github/workflows/check.yml is missing"]
    if WORKFLOW_REF not in path.read_text(encoding="utf-8", errors="replace"):
        return [f".github/workflows/check.yml does not call the reusable workflow {WORKFLOW_REF}main"]
    return []


def _check_screenshot(root: Path) -> list[str]:
    path = root / "screenshot.png"
    if not path.is_file():
        return ["screenshot.png is missing"]
    if not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
        return ["screenshot.png is not a PNG"]
    return []


def check_port(root: Path, allowed: frozenset[str]) -> list[str]:
    problems = _check_readme(root) + _check_license(root) + _check_workflow(root) + _check_screenshot(root)
    violations, _ = scan(root, allowed)
    return problems + [str(v) for v in violations]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check-port", description="Check a Deepwick port repo against the port rules.")
    parser.add_argument("path", nargs="?", default=".", type=Path, help="port repository root (default: .)")
    parser.add_argument("--palette", type=Path, help="path to palette.json (default: bundled palette)")
    args = parser.parse_args(argv)

    if not args.path.is_dir():
        print(f"check-port: not a directory: {args.path}", file=sys.stderr)
        return 2
    try:
        palette = load_palette(args.palette)
    except PaletteError as e:
        print(f"check-port: invalid palette: {e}", file=sys.stderr)
        return 2

    problems = check_port(args.path, palette.allowed_hex())
    for problem in problems:
        print(problem)
    print(f"check-port: {len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0
