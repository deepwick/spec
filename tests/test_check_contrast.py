from deepwick_spec.check_contrast import MIN_TEXT_CONTRAST, contrast_report, main
from deepwick_spec.palette import load_palette


def test_real_palette_passes(capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "comment" in out and "5.59" in out and "PASS" in out
    assert "FAIL" not in out


def test_report_covers_every_text_color():
    palette = load_palette()
    rows = contrast_report(palette)
    assert [r[0] for r in rows] == list(palette.text_colors)
    assert all(ok for *_, ok in rows)


def test_dim_text_color_fails(palette_data, write_palette, capsys):
    palette_data["colors"]["comment"] = "#2A3050"
    assert main(["--palette", str(write_palette(palette_data))]) == 1
    captured = capsys.readouterr()
    assert "FAIL" in captured.out
    assert f"below {MIN_TEXT_CONTRAST}:1" in captured.err


def test_threshold_is_inclusive_at_4_5():
    assert MIN_TEXT_CONTRAST == 4.5


def test_invalid_palette_exits_2(palette_data, write_palette, capsys):
    palette_data["ui"]["error"] = "crimson"
    assert main(["--palette", str(write_palette(palette_data))]) == 2
    assert "invalid palette" in capsys.readouterr().err


def test_missing_palette_file_exits_2(tmp_path, capsys):
    assert main(["--palette", str(tmp_path / "missing.json")]) == 2
    assert "not found" in capsys.readouterr().err
