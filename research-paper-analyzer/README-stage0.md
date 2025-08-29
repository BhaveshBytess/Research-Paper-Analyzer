# Stage 0

This stage sets up the core data contract for the project.

- A JSON Schema (`schema/paper.schema.json`) defines the canonical data structure for a research paper.
- Pydantic models (`schema/models.py`) provide Python-native validation.
- Example files (`examples/`) provide minimal and full examples of valid data.
- Tests (`tests/`) validate the examples against the Pydantic models.
