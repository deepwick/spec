import xml.etree.ElementTree as ET

from deepwick_spec.palette import load_palette
from deepwick_spec.swatches import main, render_svg

SVG = "{http://www.w3.org/2000/svg}"


def parse(svg_text):
    return ET.fromstring(svg_text)


def test_svg_is_well_formed_and_sized():
    root = parse(render_svg(load_palette()))
    assert root.tag == f"{SVG}svg"
    assert int(root.get("width")) > 0 and int(root.get("height")) > 0


def test_every_named_and_ansi_color_has_a_swatch():
    palette = load_palette()
    root = parse(render_svg(palette))
    fills = {r.get("fill") for r in root.iter(f"{SVG}rect")}
    for hex_ in [*palette.colors.values(), *palette.ansi.values()]:
        assert hex_ in fills


def test_labels_name_every_color():
    palette = load_palette()
    texts = {t.text for t in parse(render_svg(palette)).iter(f"{SVG}text")}
    for name, hex_ in palette.colors.items():
        assert name in texts and hex_ in texts
    assert "ANSI 16" in texts
    assert "Deepwick" in texts


def test_labels_use_readable_color():
    palette = load_palette()
    root = parse(render_svg(palette))
    texts = list(root.iter(f"{SVG}text"))
    white_label = next(t for t in texts if t.text == "white")
    background_label = next(t for t in texts if t.text == "background")
    assert white_label.get("fill") == palette.colors["background"]
    assert background_label.get("fill") == palette.colors["foreground"]


def test_main_writes_file(tmp_path):
    out = tmp_path / "s.svg"
    assert main(["-o", str(out)]) == 0
    parse(out.read_text(encoding="utf-8"))


def test_main_invalid_palette_exits_2(tmp_path, palette_data, write_palette, capsys):
    palette_data["colors"]["red"] = "#nothex"
    assert main(["-o", str(tmp_path / "s.svg"), "--palette", str(write_palette(palette_data))]) == 2
    assert "invalid palette" in capsys.readouterr().err


def test_committed_swatches_match_palette():
    from pathlib import Path
    svg = Path(__file__).resolve().parents[1] / "swatches.svg"
    assert svg.read_text(encoding="utf-8") == render_svg(load_palette())
