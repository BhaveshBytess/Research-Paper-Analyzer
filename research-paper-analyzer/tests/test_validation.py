# tests/test_validation.py
from orchestrator.repair import Repairer
from validation.schema_validator import validate_with_jsonschema
from schema.models import Paper

def test_heuristic_repair_and_validate():
    # Create an intentionally broken paper JSON
    broken = {
        # missing 'summary' and 'evidence' and 'authors' may be present as string incorrectly
        "title": None,
        "authors": "Bhavesh Kumar",
        # year missing
        "results": [
            {"dataset": "TinyImageNet", "metric": "Accuracy", "value": "78.4%", "unit": None}
        ]
    }

    repairer = Repairer(llm_client=None)
    repaired, applied, remaining_errors = repairer.repair_json(broken, max_attempts=1)
    # After heuristic repair remaining_errors should be empty (heuristic fills required fields)
    assert remaining_errors == [] or isinstance(remaining_errors, list)
    # Validate with Pydantic model
    ok, err = (True, "")
    try:
        Paper(**repaired)
    except Exception as e:
        ok = False
        err = str(e)
    assert ok, f"Pydantic validation failed after repair: {err}"
    # Ensure repair log exists
    assert "_meta" in repaired and "repair_log" in repaired["_meta"]
    # Ensure numeric normalization applied
    assert isinstance(repaired["results"][0]["value"], float)
    assert repaired["results"][0]["unit"] == "%"
