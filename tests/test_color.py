import pytest

from deepwick_spec.color import contrast_ratio, normalize_hex, relative_luminance


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("#04041a", "#04041a"),
        ("#04041A", "#04041a"),
        ("#fff", "#ffffff"),
        ("#ABC", "#aabbcc"),
        ("#7A86A8CC", "#7a86a8"),
        ("0x569CD6", "#569cd6"),
        ("0X569cd6", "#569cd6"),
    ],
)
def test_normalize_hex_accepts_supported_forms(raw, expected):
    assert normalize_hex(raw) == expected


@pytest.mark.parametrize("raw", ["", "#", "#12", "#1234", "#12345", "#1234567", "#ggg", "0xfff", "0x7A86A8CC", "569CD6"])
def test_normalize_hex_rejects_other_input(raw):
    with pytest.raises(ValueError):
        normalize_hex(raw)


def test_relative_luminance_extremes():
    assert relative_luminance("#000000") == 0
    assert relative_luminance("#ffffff") == pytest.approx(1.0)


def test_contrast_ratio_black_white_is_21():
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0)


def test_contrast_ratio_is_symmetric():
    assert contrast_ratio("#D4D4D4", "#04041a") == contrast_ratio("#04041a", "#D4D4D4")


@pytest.mark.parametrize(
    ("color", "expected"),
    [("#D4D4D4", 13.66), ("#7A86A8", 5.59), ("#6E7899", 4.64), ("#F44747", 5.63)],
)
def test_contrast_ratio_matches_spec_table(color, expected):
    assert round(contrast_ratio(color, "#04041a"), 2) == expected
