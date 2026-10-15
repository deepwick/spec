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
        "#1234",           # all-digit 4-digit match is an issue ref, not a color
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


from deepwick_spec.check_palette import find_colors, scan


def test_finds_alpha_forms():
    hits = list(find_colors("a #f00a b 0xff0000aa"))
    assert [(c, raw) for _, c, raw in hits] == [(3, "#f00a"), (11, "0xff0000aa")]


def test_skips_issue_refs_and_markdown_anchors():
    assert list(find_colors("see #1234 and [x](#dead)")) == []


def test_line_numbers_ignore_form_feeds():
    assert [line for line, _, _ in find_colors("a\x0cb\x1cc d\nc #ff0000\n")] == [2]


def test_skips_vendored_dirs(tmp_path):
    for d in (".venv/lib", "node_modules/x", ".git"):
        (tmp_path / d).mkdir(parents=True)
        (tmp_path / d / "a.css").write_text("color: #ff0000;\n")
    assert scan(tmp_path, frozenset()) == ([], 0)


def test_config_found_in_ancestor(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".palette-allow").write_text("#ff0000\n")
    (tmp_path / "themes").mkdir()
    (tmp_path / "themes" / "a.css").write_text("color: #ff0000;\n")
    assert scan(tmp_path / "themes" / "a.css", frozenset())[0] == []
    assert scan(tmp_path / "themes", frozenset())[0] == []


def test_ignore_patterns_relative_to_config_dir(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".palette-ignore").write_text("themes/vendor\n")
    (tmp_path / "themes" / "vendor").mkdir(parents=True)
    (tmp_path / "themes" / "vendor" / "a.css").write_text("color: #ff0000;\n")
    assert scan(tmp_path / "themes", frozenset()) == ([], 0)
