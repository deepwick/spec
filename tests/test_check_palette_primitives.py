from pathlib import PurePosixPath

import pytest

from deepwick_spec.check_palette import find_colors, is_ignored, parse_allow_file, parse_ignore_file


def raws(text):
    return [raw for _, _, raw in find_colors(text)]


@pytest.mark.parametrize(
    "text",
    ["bg=#04041a", "bg=#04041A", "fg #fff;", "x: #7A86A8CC", "color = 0x569CD6", "0X569cd6", 'c("#D4D4D4")'],
)
def test_finds_each_supported_form(text):
    assert len(raws(text)) == 1


def test_reports_line_and_column():
    text = "one\n  fg = #D4D4D4\nbg=#04041a #569CD6"
    assert list(find_colors(text)) == [(2, 8, "#D4D4D4"), (3, 4, "#04041a"), (3, 12, "#569CD6")]


@pytest.mark.parametrize(
    "text",
    [
        "&#123;",          # HTML entity
        "#abcd",           # 4 digits is not a supported form
        "#12345",          # 5 digits
        "#1234567",        # 7 digits
        "#123456789",      # 9 digits
        "id#fff",          # preceded by a word character
        "##fff",           # preceded by '#'
        "#fffz",           # followed by an alphanumeric
        "0xFF",            # byte literal, not a color
        "a0x569CD6",       # 0x inside an identifier
        "https://x.net/#palette",
    ],
)
def test_ignores_non_colors(text):
    assert raws(text) == []


def test_allow_file_parsing():
    text = "# allowed extras\n#000000  # pure black required by konsole\n\n0x123456\n#ABC\nnot-a-color\n#\n"
    assert parse_allow_file(text) == frozenset({"#000000", "#123456", "#aabbcc"})


def test_ignore_file_parsing():
    text = "# comments\n\nvendor/\n*.min.css\n  docs/legacy/*  \n"
    assert parse_ignore_file(text) == ["vendor", "*.min.css", "docs/legacy/*"]


@pytest.mark.parametrize(
    ("path", "patterns", "expected"),
    [
        ("vendor/lib/x.lua", ["vendor"], True),
        ("a/vendor/x.lua", ["vendor"], False),
        ("a/vendor/x.lua", ["*/vendor"], True),
        ("dist/app.min.css", ["*.min.css"], True),
        ("docs/legacy/old.md", ["docs/legacy/*"], True),
        ("docs/new.md", ["docs/legacy/*"], False),
        ("theme.toml", [], False),
    ],
)
def test_is_ignored(path, patterns, expected):
    assert is_ignored(PurePosixPath(path), patterns) is expected
