import argparse
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from deepwick_spec.color import contrast_ratio
from deepwick_spec.palette import Palette, PaletteError, load_palette

SWATCH_W = 180
SWATCH_H = 90
GAP = 12
COLS = 8
PAD = 32


def _label_color(palette: Palette, hex_: str) -> str:
    fg = palette.colors["foreground"]
    bg = palette.colors["background"]
    return fg if contrast_ratio(hex_, fg) >= contrast_ratio(hex_, bg) else bg


def _grid(parts: list[str], palette: Palette, items: list[tuple[str, str]], y0: int) -> int:
    for i, (name, hex_) in enumerate(items):
        row, col = divmod(i, COLS)
        x = PAD + col * (SWATCH_W + GAP)
        y = y0 + row * (SWATCH_H + GAP)
        label = _label_color(palette, hex_)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{SWATCH_W}" height="{SWATCH_H}" rx="8" '
            f'fill="{hex_}" stroke="{palette.colors["overlay"]}"/>'
        )
        parts.append(f'<text x="{x + 14}" y="{y + 38}" fill="{label}" font-family="monospace" font-size="16">{escape(name)}</text>')
        parts.append(f'<text x="{x + 14}" y="{y + 64}" fill="{label}" font-family="monospace" font-size="14">{hex_}</text>')
    rows = -(-len(items) // COLS)
    return y0 + rows * (SWATCH_H + GAP)


def _heading(parts: list[str], palette: Palette, text: str, y: int, size: int) -> None:
    parts.append(
        f'<text x="{PAD}" y="{y}" fill="{palette.colors["foreground"]}" '
        f'font-family="sans-serif" font-size="{size}" font-weight="bold">{escape(text)}</text>'
    )


def render_svg(palette: Palette) -> str:
    width = PAD * 2 + COLS * SWATCH_W + (COLS - 1) * GAP
    parts: list[str] = []
    _heading(parts, palette, palette.name, PAD + 28, 28)
    y = _grid(parts, palette, list(palette.colors.items()), PAD + 56)
    _heading(parts, palette, "ANSI 16", y + 28, 20)
    y = _grid(parts, palette, list(palette.ansi.items()), y + 48)
    height = y - GAP + PAD
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'<rect width="100%" height="100%" fill="{palette.colors["background"]}"/>',
            *parts,
            "</svg>",
        ]
    ) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="deepwick-swatches", description="Render the Deepwick palette as an SVG.")
    parser.add_argument("-o", "--output", type=Path, default=Path("swatches.svg"))
    parser.add_argument("--palette", type=Path, help="path to palette.json (default: bundled palette)")
    args = parser.parse_args(argv)
    try:
        palette = load_palette(args.palette)
    except PaletteError as e:
        print(f"deepwick-swatches: invalid palette: {e}", file=sys.stderr)
        return 2
    args.output.write_text(render_svg(palette), encoding="utf-8")
    return 0
