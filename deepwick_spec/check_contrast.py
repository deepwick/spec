import argparse
import sys
from pathlib import Path

from deepwick_spec.color import contrast_ratio
from deepwick_spec.palette import Palette, PaletteError, load_palette

MIN_TEXT_CONTRAST = 4.5


def contrast_report(palette: Palette) -> list[tuple[str, str, float, bool]]:
    background = palette.colors["background"]
    rows = []
    for name in palette.text_colors:
        hex_ = palette.colors[name]
        ratio = contrast_ratio(hex_, background)
        rows.append((name, hex_, ratio, ratio >= MIN_TEXT_CONTRAST))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check-contrast",
        description=f"Check that every Deepwick text color is at least {MIN_TEXT_CONTRAST}:1 on the background.",
    )
    parser.add_argument("--palette", type=Path, help="path to palette.json (default: bundled palette)")
    args = parser.parse_args(argv)

    try:
        palette = load_palette(args.palette)
    except PaletteError as e:
        print(f"check-contrast: invalid palette: {e}", file=sys.stderr)
        return 2

    rows = contrast_report(palette)
    print(f"{'name':<12} {'hex':<8} {'ratio':>6}  result")
    for name, hex_, ratio, ok in rows:
        print(f"{name:<12} {hex_:<8} {ratio:>6.2f}  {'PASS' if ok else 'FAIL'}")

    failures = [row for row in rows if not row[3]]
    if failures:
        print(f"{len(failures)} text color(s) below {MIN_TEXT_CONTRAST}:1 on background", file=sys.stderr)
        return 1
    return 0
