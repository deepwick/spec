import pytest

from deepwick_spec.ansi import line_with, plain, runs, style_of

E = "\x1b["


def test_truecolor_and_attributes():
    text = f"{E}3;38;2;122;134;168m# note{E}0m {E}1;48;2;38;79;120mx{E}0m"
    assert style_of(text, "# note") == {"fg": "#7a86a8", "bg": None, "bold": False, "italic": True, "underline": False, "reverse": False}
    assert style_of(text, "x")["bg"] == "#264f78"
    assert style_of(text, "x")["bold"] is True


def test_basic_and_256_colors_and_resets():
    text = f"{E}31mred{E}39mdefault{E}95mpink{E}38;5;208morange{E}0m"
    assert style_of(text, "red")["fg"] == "ansi:1"
    assert style_of(text, "default")["fg"] is None
    assert style_of(text, "pink")["fg"] == "ansi:13"
    assert style_of(text, "orange")["fg"] == "ansi256:208"


def test_attribute_off_codes():
    text = f"{E}1;3;4;7mon{E}22;23;24;27moff"
    on, off = style_of(text, "on"), style_of(text, "off")
    assert (on["bold"], on["italic"], on["underline"], on["reverse"]) == (True, True, True, True)
    assert (off["bold"], off["italic"], off["underline"], off["reverse"]) == (False, False, False, False)


def test_colon_subparameters():
    text = f"{E}4:3mcurly{E}0m{E}38:2::86:156:214mblue{E}0m"
    assert style_of(text, "curly")["underline"] is True
    assert style_of(text, "curly")["italic"] is False
    assert style_of(text, "blue")["fg"] == "#569cd6"


def test_empty_sgr_resets():
    assert style_of(f"{E}31mred{E}mplain", "plain")["fg"] is None


def test_style_persists_across_newlines():
    assert [s["fg"] for _, s in runs(f"{E}32ma\nb{E}0m")] == ["ansi:2"]


def test_plain_and_line_with():
    text = f"one\n{E}31mtwo{E}0m three\n"
    assert plain(text) == "one\ntwo three\n"
    assert line_with(text, "two three") == f"{E}31mtwo{E}0m three"


def test_missing_token_raises():
    with pytest.raises(AssertionError, match="nope"):
        style_of("abc", "nope")
