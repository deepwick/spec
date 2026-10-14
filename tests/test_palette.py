import pytest

from deepwick_spec.palette import (
    ANSI_KEYS,
    PaletteError,
    SyntaxStyle,
    default_palette_path,
    load_palette,
    parse_palette,
)


def test_default_path_points_at_repo_palette():
    assert default_palette_path().name == "palette.json"
    assert default_palette_path().is_file()


def test_load_real_palette():
    palette = load_palette()
    assert palette.name == "Deepwick"
    assert palette.colors["background"] == "#04041a"
    assert palette.colors["comment"] == "#7A86A8"
    assert palette.syntax["comment"] == SyntaxStyle("comment", ("italic",))
    assert palette.syntax["bold"] == SyntaxStyle(None, ("bold",))


def test_ansi_normal_slots_reuse_named_colors():
    palette = load_palette()
    c = palette.colors
    expected = {
        "black": c["overlay"], "red": c["red"], "green": c["green"], "yellow": c["yellow"],
        "blue": c["blue"], "magenta": c["magenta"], "cyan": c["teal"], "white": c["foreground"],
        "brightBlack": c["muted"], "brightBlue": c["lightBlue"], "brightWhite": c["white"],
    }
    for slot, hex_ in expected.items():
        assert palette.ansi[slot] == hex_, slot


def test_allowed_hex_is_normalized_union_of_colors_and_ansi():
    allowed = load_palette().allowed_hex()
    assert "#04041a" in allowed
    assert "#7a86a8" in allowed
    assert "#ff7a7a" in allowed  # bright-only ANSI value
    assert "#57a64a" in allowed
    assert all(h == h.lower() and len(h) == 7 for h in allowed)


def test_ansi_keys_are_the_16_slots():
    assert len(ANSI_KEYS) == 16
    assert ANSI_KEYS[0] == "black" and ANSI_KEYS[-1] == "brightWhite"


def test_missing_file_raises_palette_error(tmp_path):
    with pytest.raises(PaletteError, match="not found"):
        load_palette(tmp_path / "nope.json")


def test_invalid_json_raises_palette_error(tmp_path):
    path = tmp_path / "palette.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(PaletteError, match="invalid JSON"):
        load_palette(path)


def test_missing_top_level_key(palette_data):
    del palette_data["ui"]
    with pytest.raises(PaletteError, match="missing top-level key: ui"):
        parse_palette(palette_data)


def test_bad_hex_in_colors(palette_data):
    palette_data["colors"]["blue"] = "#569CD"
    with pytest.raises(PaletteError, match=r"colors\.blue"):
        parse_palette(palette_data)


def test_short_hex_not_allowed_in_palette(palette_data):
    palette_data["colors"]["white"] = "#fff"
    with pytest.raises(PaletteError, match=r"colors\.white"):
        parse_palette(palette_data)


def test_missing_required_color(palette_data):
    del palette_data["colors"]["overlay"]
    palette_data["ui"]["inactiveBorder"] = "surface"
    palette_data["ansi"]["black"] = "#10192C"
    with pytest.raises(PaletteError, match="required color 'overlay'"):
        parse_palette(palette_data)


def test_missing_ansi_slot(palette_data):
    del palette_data["ansi"]["brightCyan"]
    with pytest.raises(PaletteError, match="brightCyan"):
        parse_palette(palette_data)


def test_bad_hex_in_ansi(palette_data):
    palette_data["ansi"]["red"] = "red"
    with pytest.raises(PaletteError, match=r"ansi\.red"):
        parse_palette(palette_data)


@pytest.mark.parametrize("section", ["ui", "terminal"])
def test_dangling_name_reference(palette_data, section):
    key = next(iter(palette_data[section]))
    palette_data[section][key] = "chartreuse"
    with pytest.raises(PaletteError, match=f"{section}\\.{key}: unknown color name 'chartreuse'"):
        parse_palette(palette_data)


def test_dangling_syntax_reference(palette_data):
    palette_data["syntax"]["keyword"]["color"] = "navy"
    with pytest.raises(PaletteError, match=r"syntax\.keyword\.color"):
        parse_palette(palette_data)


def test_unknown_syntax_style(palette_data):
    palette_data["syntax"]["comment"]["style"] = ["italic", "blink"]
    with pytest.raises(PaletteError, match="blink"):
        parse_palette(palette_data)


def test_dangling_text_color(palette_data):
    palette_data["textColors"].append("ultraviolet")
    with pytest.raises(PaletteError, match="textColors"):
        parse_palette(palette_data)


def test_load_palette_from_explicit_path(palette_data, write_palette):
    palette_data["name"] = "Test"
    assert load_palette(write_palette(palette_data)).name == "Test"
