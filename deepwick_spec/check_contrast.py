import argparse
import sys
from pathlib import Path

from deepwick_spec.color import contrast_ratio
from deepwick_spec.palette import Palette, PaletteError, load_palette
from deepwick_spec.xterm256 import index_hex

MIN_TEXT_CONTRAST = 4.5
FOREGROUND_BACKGROUNDS = ("selection", "diffAdded", "diffRemoved", "diffChanged", "diffAddedEmph", "diffRemovedEmph", "diffText")


def contrast_report(palette: Palette) -> list[tuple[str, str, float, bool]]:
    background = palette.colors["background"]
    rows = []
    for name in palette.text_colors:
        hex_ = palette.colors[name]
        ratio = contrast_ratio(hex_, background)
        rows.append((name, hex_, ratio, ratio >= MIN_TEXT_CONTRAST))
    return rows


def xterm256_report(palette: Palette) -> list[tuple[str, str, float, bool]]:
    """Contrast of the 256-color palette, using each index's real color."""
    xt = palette.xterm256
    pairs = [(f"text {name}", name, "background") for name in palette.text_colors]
    pairs += [(f"foreground on {name}", "foreground", name) for name in FOREGROUND_BACKGROUNDS]
    rows = []
    for label, fg, bg in pairs:
        ratio = contrast_ratio(index_hex(xt[fg]), index_hex(xt[bg]))
        rows.append((label, f"{xt[fg]}/{xt[bg]}", ratio, ratio >= MIN_TEXT_CONTRAST))
    return rows


def duplicate_indices(palette: Palette) -> dict[int, list[str]]:
    """xterm256 indices shared by more than one color."""
    by_index: dict[int, list[str]] = {}
    for name, index in palette.xterm256.items():
        by_index.setdefault(index, []).append(name)
    return {index: names for index, names in by_index.items() if len(names) > 1}


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

    xt_rows = xterm256_report(palette)
    print(f"\n{'256-color pair':<30} {'fg/bg':<8} {'ratio':>6}  result")
    for label, pair, ratio, ok in xt_rows:
        print(f"{label:<30} {pair:<8} {ratio:>6.2f}  {'PASS' if ok else 'FAIL'}")

    status = 0
    failures = [row for row in rows if not row[3]]
    if failures:
        print(f"{len(failures)} text color(s) below {MIN_TEXT_CONTRAST}:1 on background", file=sys.stderr)
        status = 1
    for index, names in duplicate_indices(palette).items():
        print(f"256-color index {index} is shared by {', '.join(names)}", file=sys.stderr)
        status = 1
    xt_failures = [row for row in xt_rows if not row[3]]
    if xt_failures:
        print(f"{len(xt_failures)} 256-color pair(s) below {MIN_TEXT_CONTRAST}:1", file=sys.stderr)
        status = 1
    return status
