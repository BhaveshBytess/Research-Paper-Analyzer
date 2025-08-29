# normalizers/number_parser.py
import re
from typing import Tuple, Optional, Union

Number = Union[float, int]

_PERCENT_RE = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*%?\s*$")
_FLOAT_RE = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)(?:\s*e[+-]?\d+)?\s*$", re.I)

def parse_number_string(s: Union[str, Number]) -> Tuple[Optional[float], Optional[str]]:
    """
    Parse a numeric string into (value, unit).
    - '92.1%' -> (92.1, '%')
    - '0.921' -> (0.921, None)
    - 78.4 -> (78.4, None)
    Returns (None, None) if parsing fails.
    """
    # if already a number
    if s is None:
        return None, None
    if isinstance(s, (int, float)):
        return float(s), None

    text = str(s).strip()
    if text == "":
        return None, None

    # explicit percent sign
    if "%" in text:
        # Extract numeric portion
        m = re.search(r"([+-]?\d+(?:\.\d+)?)", text)
        if m:
            try:
                return float(m.group(1)), "%"
            except Exception:
                return None, None

    # pure numeric (maybe with whitespace)
    m = _FLOAT_RE.match(text)
    if m:
        try:
            return float(m.group(1)), None
        except Exception:
            return None, None

    # fallback: find first numeric token
    m = re.search(r"([+-]?\d+(?:\.\d+)?)", text)
    if m:
        try:
            return float(m.group(1)), None
        except Exception:
            return None, None

    return None, None


def normalize_result_record(rec: dict) -> dict:
    """
    Normalize a single result record in-place:
    - If rec['value'] is a string, parse to float and set rec['unit'] if percent.
    - Ensure rec['value'] is numeric (float) if possible.
    Returns modified record.
    """
    if not isinstance(rec, dict):
        return rec
    val = rec.get("value", None)
    if val is None:
        return rec
    v, u = parse_number_string(val)
    if v is not None:
        rec["value"] = float(v)
        # set unit only if parsed a unit and existing unit missing or inconsistent
        if u:
            rec["unit"] = u
    # If unit present and has percent symbol in string, normalize to "%"
    unit = rec.get("unit")
    if isinstance(unit, str) and "%" in unit and unit != "%":
        rec["unit"] = "%"
    return rec
