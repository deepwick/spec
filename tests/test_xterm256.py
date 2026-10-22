import pytest

from deepwick_spec.palette import load_palette
from deepwick_spec.xterm256 import index_hex, nearest_index


def test_cube_and_ramp_corners():
    assert index_hex(16) == "#000000"
    assert index_hex(231) == "#ffffff"
    assert index_hex(67) == "#5f87af"
    assert index_hex(232) == "#080808"
    assert index_hex(255) == "#eeeeee"


def test_exact_colors_round_trip():
    assert all(nearest_index(index_hex(i)) == i for i in range(16, 256))


def test_never_returns_terminal_palette_slots():
    for value in ("#000000", "#800000", "#ffffff", "#c0c0c0", "#ff0000"):
        assert 16 <= nearest_index(value) <= 255


def test_out_of_range_rejected():
    for bad in (0, 15, 256):
        with pytest.raises(ValueError):
            index_hex(bad)


def test_accepts_any_normalizable_hex():
    assert nearest_index("#FFF") == nearest_index("0xffffff") == 231


def test_every_palette_color_maps_and_blues_stay_distinct():
    colors = load_palette().colors
    indices = {name: nearest_index(value) for name, value in colors.items()}
    assert all(16 <= i <= 255 for i in indices.values())
    assert len({indices["blue"], indices["cyan"], indices["teal"]}) == 3
