# validation/schema_validator.py
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any
from jsonschema import Draft7Validator

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "paper.schema.json"
_schema = json.loads(open(SCHEMA_PATH, "r", encoding="utf-8").read())
_validator = Draft7Validator(_schema)

def validate_with_jsonschema(data: Dict[str, Any]) -> List[str]:
    """
    Returns a list of human-readable validation error strings; empty list means valid.
    """
    errors = []
    for err in _validator.iter_errors(data):
        # Build the path
        path = ".".join([str(p) for p in err.absolute_path]) if err.absolute_path else "(root)"
        errors.append(f"{path}: {err.message}")
    return errors


def validate_with_pydantic(data: Dict[str, Any], model_cls) -> Tuple[bool, str]:
    """
    Validate by parsing into Pydantic model. Returns (is_valid, error_message_or_empty).
    """
    try:
        model_cls(**data)
        return True, ""
    except Exception as e:
        return False, str(e)
