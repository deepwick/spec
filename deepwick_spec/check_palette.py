import re
from collections.abc import Iterator
from fnmatch import fnmatch
from pathlib import PurePosixPath

from deepwick_spec.color import normalize_hex

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
