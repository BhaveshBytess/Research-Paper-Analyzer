# tests/test_schema.py
import json
from pathlib import Path
import sys
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schema.models import Paper

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

def load_json(name):
    p = EXAMPLES_DIR / name
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def test_minimal_example_parses():
    data = load_json("example_minimal.json")
    paper = Paper(**data)
    assert paper.title and isinstance(paper.title, str)

def test_full_example_parses():
    data = load_json("example_full.json")
    paper = Paper(**data)
    assert paper.results and len(paper.results) > 0
    # check a numeric field
    first_result = paper.results[0]
    assert isinstance(first_result.value, float) or isinstance(first_result.value, int)
