import py_compile
import shutil
import subprocess
from pathlib import Path

import pytest

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def test_python_sample_compiles(tmp_path):
    py_compile.compile(str(SAMPLES / "sample.py"), cfile=str(tmp_path / "s.pyc"), doraise=True)


@pytest.mark.parametrize(
    ("name", "markers"),
    [
        ("sample.py", ["# ", '"""', "class ", "@dataclass", "Protocol", "Enum", "re.compile", "\\n", "MAX_RETRIES", "if ", "import "]),
        ("sample.ts", ["// ", "interface ", "enum ", "<T>", "class ", "this.", "/^", "`", "import ", "0x2a"]),
        ("sample.c", ["#include", "#define", "SQUARE(", "struct ", "goto ", "done:"]),
        ("sample.md", ["# ", "**", "*italic*", "`inline code`", "](https://", "<kbd>", "~~"]),
    ],
)
def test_samples_exercise_syntax_roles(name, markers):
    text = (SAMPLES / name).read_text(encoding="utf-8")
    for marker in markers:
        assert marker in text, f"{name} lacks {marker!r}"


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_c_sample_compiles():
    subprocess.run(["cc", "-fsyntax-only", "-Wall", "-Werror", str(SAMPLES / "sample.c")], check=True)


def test_terminal_script_runs():
    result = subprocess.run(["bash", str(SAMPLES / "terminal.sh")], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    for marker in ["ANSI 16", "\x1b[31m", "\x1b[97m", "$ ls -lgoA", "diff --git", "Merge branch feature"]:
        assert marker in result.stdout, marker


def test_samples_contain_no_hex_colors():
    from deepwick_spec.check_palette import find_colors

    for path in SAMPLES.iterdir():
        assert list(find_colors(path.read_text(encoding="utf-8"))) == [], path.name


def test_terminal_script_hides_user_and_group():
    import getpass

    result = subprocess.run(["bash", str(SAMPLES / "terminal.sh")], capture_output=True, text=True, timeout=60)
    assert getpass.getuser() not in result.stdout
