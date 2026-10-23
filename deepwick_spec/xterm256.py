"""xterm-256 helpers for the fixed part of the palette (16-255).

Ports read Deepwick's hand-picked 256-color palette from `Palette.xterm256`. `nearest_index` only
proposes picks (plain RGB distance) when that palette is revised; no port should call it.
Indices 0-15 are left out: terminals theme them, so they only match under a Deepwick terminal theme.
"""
from deepwick_spec.color import normalize_hex

_LEVELS = (0, 95, 135, 175, 215, 255)


def index_hex(index: int) -> str:
    if not 16 <= index <= 255:
        raise ValueError(f"not a fixed xterm-256 index (16-255): {index}")
    if index >= 232:
        rgb = (8 + 10 * (index - 232),) * 3
    else:
        n = index - 16
        rgb = (_LEVELS[n // 36], _LEVELS[n // 6 % 6], _LEVELS[n % 6])
    return "#" + "".join(f"{c:02x}" for c in rgb)


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = normalize_hex(hex_color)
    return tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))


_TABLE = [(i, _rgb(index_hex(i))) for i in range(16, 256)]


def nearest_index(hex_color: str) -> int:
    target = _rgb(hex_color)
    return min(_TABLE, key=lambda entry: sum((a - b) ** 2 for a, b in zip(entry[1], target)))[0]
