import argparse
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

from deepwick_spec.color import normalize_hex
from deepwick_spec.palette import PaletteError, load_palette

ALLOW_FILE = ".palette-allow"
IGNORE_FILE = ".palette-ignore"

_COLOR = re.compile(
    r"(?<![\w&#])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9A-Za-z_])"
    r"|(?<!\w)0[xX][0-9a-fA-F]{6}(?![0-9A-Za-z_])"
)


def find_colors(text: str) -> Iterator[tuple[int, int, str]]:
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in _COLOR.finditer(line):
            yield lineno, match.start() + 1, match.group(0)


def parse_allow_file(text: str) -> frozenset[str]:
    allowed = set()
    for line in text.splitlines():
        tokens = line.split()
        if not tokens:
            continue
        try:
            allowed.add(normalize_hex(tokens[0]))
        except ValueError:
            continue
    return frozenset(allowed)


def parse_ignore_file(text: str) -> list[str]:
    patterns = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(line.rstrip("/"))
    return patterns


def is_ignored(rel: PurePosixPath, patterns: list[str]) -> bool:
    candidates = [rel.as_posix()] + [p.as_posix() for p in rel.parents if p != PurePosixPath(".")]
    return any(fnmatch(candidate, pattern) for candidate in candidates for pattern in patterns)


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    col: int
    raw: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}:{self.col}: {self.raw} not in Deepwick palette"


def _read_config(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _iter_files(root: Path, patterns: list[str]) -> Iterator[Path]:
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = PurePosixPath(path.relative_to(root).as_posix())
        if ".git" in rel.parts or rel.name in (ALLOW_FILE, IGNORE_FILE):
            continue
        if is_ignored(rel, patterns):
            continue
        yield path


def _read_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", errors="replace")


def scan(root: Path, allowed: frozenset[str]) -> tuple[list[Violation], int]:
    config_dir = root if root.is_dir() else root.parent
    permitted = allowed | parse_allow_file(_read_config(config_dir / ALLOW_FILE))
    patterns = parse_ignore_file(_read_config(config_dir / IGNORE_FILE))

    violations = []
    checked = 0
    for path in _iter_files(root, patterns):
        try:
            text = _read_text(path)
        except OSError as e:
            print(f"check-palette: warning: cannot read {path}: {e.strerror}", file=sys.stderr)
            continue
        if text is None:
            continue
        checked += 1
        shown = path.relative_to(root).as_posix() if root.is_dir() else str(path)
        for line, col, raw in find_colors(text):
            if normalize_hex(raw) not in permitted:
                violations.append(Violation(shown, line, col, raw))
    return violations, checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check-palette",
        description="Report hex colors that are not in the Deepwick palette.",
    )
    parser.add_argument("path", nargs="?", default=".", type=Path, help="file or directory to scan (default: .)")
    parser.add_argument("--palette", type=Path, help="path to palette.json (default: bundled palette)")
    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"check-palette: no such file or directory: {args.path}", file=sys.stderr)
        return 2
    try:
        palette = load_palette(args.palette)
    except PaletteError as e:
        print(f"check-palette: invalid palette: {e}", file=sys.stderr)
        return 2

    violations, checked = scan(args.path, palette.allowed_hex())
    for violation in violations:
        print(violation)
    print(f"check-palette: {len(violations)} violation(s) in {checked} file(s)", file=sys.stderr)
    return 1 if violations else 0
