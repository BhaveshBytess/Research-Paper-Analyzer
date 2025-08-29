# schema/validate_json.py
import json
from jsonschema import validate, RefResolver
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "paper.schema.json"

def validate_file(json_path):
    schema = json.loads(open(SCHEMA_PATH).read())
    data = json.loads(open(json_path).read())
    validate(instance=data, schema=schema)
    print(f"{json_path} validated OK")

if __name__ == "__main__":
    import sys
    validate_file(sys.argv[1])
