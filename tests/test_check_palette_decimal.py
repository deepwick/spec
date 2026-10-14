import pytest

from deepwick_spec.check_palette import find_colors, parse_allow_file, scan, to_hex
from deepwick_spec.palette import load_palette

ALLOWED = load_palette().allowed_hex()


def found(text):
    return [(col, raw) for _, col, raw in find_colors(text)]


@pytest.mark.parametrize(
    ("text", "raw", "hex_"),
    [
        ("color: rgb(4,4,26);", "rgb(4,4,26)", "#04041a"),
        ("color: RGBA( 4, 4, 26, 0.5 );", "RGBA( 4, 4, 26, 0.5 )", "#04041a"),
        ("bg='rgb(212, 212, 212)'", "rgb(212, 212, 212)", "#d4d4d4"),
        ("Color=4,4,26", "4,4,26", "#04041a"),
        ("Color = 205, 49, 49", "205, 49, 49", "#cd3131"),
    ],
)
def test_detects_decimal_forms(text, raw, hex_):
    assert [r for _, r in found(text)] == [raw]
    assert to_hex(raw) == hex_


def test_key_value_column_points_at_value():
    assert found("Color=4,4,26") == [(7, "4,4,26")]


@pytest.mark.parametrize(
    "text",
    [
        "x = [1,2,3]",
        "version 1,2,3",
        "Color=4,4,26,255",
        "# Color=1,2,3",
        "; Color=1,2,3",
        "Color=256,0,0",
        "rgb(300,0,0)",
        "foo(1,2,3)",
        "point = 1,2,3 # trailing",
    ],
)
def test_ignores_non_colors(text):
    assert found(text) == []


def test_mixed_forms_are_ordered_by_column():
    assert found("a=#04041a b=rgb(4,4,26)") == [(3, "#04041a"), (13, "rgb(4,4,26)")]


def test_to_hex_still_handles_hex():
    assert to_hex("#FFF") == "#ffffff"


def test_konsole_style_file(tmp_path):
    (tmp_path / "Deepwick.colorscheme").write_text("[Background]\nColor=4,4,26\n\n[Color1]\nColor=205,49,49\n")
    violations, checked = scan(tmp_path, ALLOWED)
    assert checked == 1
    assert [str(v) for v in violations] == ["Deepwick.colorscheme:5:7: 205,49,49 not in Deepwick palette"]


def test_allow_file_accepts_decimal_triples():
    assert parse_allow_file("0,0,0  # pure black\n255, 255, 255\n#123456\n") == frozenset({"#000000", "#ffffff", "#123456"})
