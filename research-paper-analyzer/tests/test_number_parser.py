# tests/test_number_parser.py
from normalizers.number_parser import parse_number_string, normalize_result_record

def test_parse_percent():
    v, u = parse_number_string("78.4%")
    assert v == 78.4
    assert u == "%"

def test_parse_float():
    v, u = parse_number_string("0.921")
    assert abs(v - 0.921) < 1e-9
    assert u is None

def test_normalize_record_percent():
    rec = {"dataset": "TinyImageNet", "metric": "Accuracy", "value": "78.4%", "unit": None}
    rec2 = normalize_result_record(rec)
    assert isinstance(rec2["value"], float)
    assert rec2["unit"] == "%"
