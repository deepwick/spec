import argparse
import os
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

SKIP_DIRS = frozenset({".git", ".venv", "node_modules"})

_COLOR = re.compile(
    r"(?<![\w&#])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})(?![0-9A-Za-z_])"
    r"|(?<!\w)0[xX](?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6})(?![0-9A-Za-z_])"
)


def _skip(line: str, start: int, raw: str) -> bool:
    """4-digit #matches that are issue refs (#1234) or Markdown anchors (](#dead))."""
    return raw.startswith("#") and len(raw) == 5 and (raw[1:].isdigit() or line[max(0, start - 2) : start] == "](")


_RGB_FUNC = re.compile(
    r"(?<![\w-])rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*[\d.]+%?\s*)?\)",
    re.IGNORECASE,
)
_RGB_VALUE = re.compile(r"^\s*[^\s=#;][^=]*=\s*((\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3}))\s*$")
_TRIPLE = re.compile(r"(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})")


def _in_range(*components: str) -> bool:
    return all(int(c) <= 255 for c in components)


def to_hex(raw: str) -> str:
    if raw.startswith("#") or raw[:2].lower() == "0x":
        return normalize_hex(raw)
    match = _TRIPLE.search(raw)
    if not match or not _in_range(*match.groups()):
        raise ValueError(f"not a color: {raw!r}")
    return "#" + "".join(f"{int(c):02x}" for c in match.groups())


def find_colors(text: str) -> Iterator[tuple[int, int, str]]:
    for lineno, line in enumerate(text.split("\n"), start=1):
        hits = [(m.start(), m.group(0)) for m in _COLOR.finditer(line) if not _skip(line, m.start(), m.group(0))]
        hits += [(m.start(), m.group(0)) for m in _RGB_FUNC.finditer(line) if _in_range(*m.groups())]
        value = _RGB_VALUE.match(line)
        if value and _in_range(*value.groups()[1:]):
            hits.append((value.start(1), value.group(1)))
        for start, raw in sorted(hits):
            yield lineno, start + 1, raw


def parse_allow_file(text: str) -> frozenset[str]:
    allowed = set()
    for line in text.splitlines():
        tokens = line.split()
        if not tokens:
            continue
        candidate = tokens[0] if tokens[0].startswith(("#", "0x", "0X")) else line.split("#")[0]
        try:
            allowed.add(to_hex(candidate.strip()))
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


def _config_dir(root: Path) -> Path:
    """Nearest directory with a config file, searching up to the repo root (none above it, none without a repo)."""
    start = (root if root.is_dir() else root.parent).absolute()
    chain = [start, *start.parents]
    top = next((i for i, d in enumerate(chain) if (d / ".git").exists()), None)
    for directory in chain[: top + 1] if top is not None else [start]:
        if (directory / ALLOW_FILE).is_file() or (directory / IGNORE_FILE).is_file():
            return directory
    return start


def _warn_unreadable(error: OSError) -> None:
    print(f"check-palette: warning: cannot read {error.filename}: {error.strerror}", file=sys.stderr)


def _iter_files(root: Path, base: Path, patterns: list[str]) -> Iterator[Path]:
    if root.is_file():
        if not is_ignored(PurePosixPath(root.relative_to(base).as_posix()), patterns):
            yield root
        return
    found = []
    for dirpath, dirnames, filenames in os.walk(root, onerror=_warn_unreadable):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            if not path.is_file() or name in (ALLOW_FILE, IGNORE_FILE) or name in SKIP_DIRS:
                continue
            if is_ignored(PurePosixPath(path.relative_to(base).as_posix()), patterns):
                continue
            found.append(path)
    yield from sorted(found)


def _read_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", errors="replace")


def scan(root: Path, allowed: frozenset[str]) -> tuple[list[Violation], int]:
    config_dir = _config_dir(root)
    permitted = allowed | parse_allow_file(_read_config(config_dir / ALLOW_FILE))
    patterns = parse_ignore_file(_read_config(config_dir / IGNORE_FILE))

    violations = []
    checked = 0
    abs_root = root.absolute()
    for path in _iter_files(abs_root, config_dir, patterns):
        try:
            text = _read_text(path)
        except OSError as e:
            print(f"check-palette: warning: cannot read {path}: {e.strerror}", file=sys.stderr)
            continue
        if text is None:
            continue
        checked += 1
        shown = path.relative_to(abs_root).as_posix() if root.is_dir() else str(root)
        for line, col, raw in find_colors(text):
            if to_hex(raw) not in permitted:
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
    if not (args.path.is_file() or args.path.is_dir()):
        print(f"check-palette: not a regular file or directory: {args.path}", file=sys.stderr)
        return 2
    if not os.access(args.path, os.R_OK | (os.X_OK if args.path.is_dir() else 0)):
        print(f"check-palette: cannot read {args.path}", file=sys.stderr)
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
