import copy
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
_REAL = json.loads((REPO / "palette.json").read_text(encoding="utf-8"))


@pytest.fixture
def palette_data():
    return copy.deepcopy(_REAL)


@pytest.fixture
def write_palette(tmp_path):
    def write(data):
        path = tmp_path / "palette.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    return write
