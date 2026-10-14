import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("uv") is None, reason="requires uv")
def test_installed_wheel_bundles_palette_and_runs(tmp_path):
    dist = tmp_path / "dist"
    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(dist), str(REPO)], check=True, capture_output=True)
    wheel = next(dist.glob("*.whl"))
    with zipfile.ZipFile(wheel) as zf:
        assert "deepwick_spec/palette.json" in zf.namelist()

    venv = tmp_path / "venv"
    subprocess.run(["uv", "venv", "--quiet", str(venv)], check=True)
    subprocess.run(
        ["uv", "pip", "install", "--quiet", "--python", str(venv / "bin" / "python"), str(wheel)],
        check=True,
    )

    port = tmp_path / "port"
    port.mkdir()
    (port / "theme.conf").write_text("bg = #04041a\n")
    result = subprocess.run(
        [str(venv / "bin" / "check-palette"), str(port)], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr

    (port / "theme.conf").write_text("bg = #123456\n")
    result = subprocess.run(
        [str(venv / "bin" / "check-palette"), str(port)], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 1
