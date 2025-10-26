# orchestrator/repair.py
import copy
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from pathlib import Path
import json

from validation.schema_validator import validate_with_jsonschema
from normalizers.number_parser import normalize_result_record, parse_number_string
from schema.models import Paper

# Optional: import MockLLM if you want to later invoke LLM-based repair:
from orchestrator.heads import MockLLM

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "paper.schema.json"

class Repairer:
    def __init__(self, schema_path: str = None, llm_client=None):
        self.schema_path = schema_path or str(SCHEMA_PATH)
        self.llm = llm_client  # may be None or MockLLM/real client

    def heuristic_repair(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Deterministic, auditable heuristic repairs:
        - Fill missing required top-level fields with conservative placeholders.
        - Normalize numeric results if present.
        - Add repair_log containing human-readable entries describing each change.
        Returns (repaired_data, list_of_repair_messages).
        """
        repaired = copy.deepcopy(data) if data is not None else {}
        repairs: List[str] = []
        # Ensure top-level structure
        if not isinstance(repaired, dict):
            repaired = {}
            repairs.append("root object was not a dict; replaced with empty dict")

        # Ensure required fields exist:
        # From Stage 0 schema, required = ["title","authors","year","summary","evidence"]
        # We'll add conservative placeholders but explicitly log them for human review.
        now_year = datetime.now(timezone.utc).year
        required_defaults = {
            "title": "UNKNOWN_TITLE_REPAIRED",
            "authors": [],
            "year": now_year,
            "summary": "SUMMARY_MISSING: automatic placeholder — please review.",
            "evidence": {}
        }

        for field, default in required_defaults.items():
            if field not in repaired or repaired.get(field) is None:
                repaired[field] = default
                repairs.append(f"Inserted placeholder for required field '{field}'")

        # Normalize results list numeric values
        results = repaired.get("results", [])
        if isinstance(results, list):
            for i, rec in enumerate(results):
                if isinstance(rec, dict):
                    before = rec.get("value")
                    normalize_result_record(rec)
                    after = rec.get("value")
                    if before != after:
                        repairs.append(f"Normalized numeric value in results[{i}] from '{before}' to {after}")

        # Safety: ensure 'authors' is list
        if not isinstance(repaired.get("authors"), list):
            repaired["authors"] = [str(repaired.get("authors"))] if repaired.get("authors") else []
            repairs.append("Normalized 'authors' to a list")

        # Add a repair log inside the JSON so later auditing is easy
        repaired.setdefault("_meta", {})
        repaired["_meta"].setdefault("repair_log", [])
        repaired["_meta"]["repair_log"].extend(repairs)
        repaired["_meta"]["repaired_at"] = datetime.now(timezone.utc).isoformat()

        return repaired, repairs

    def repair_json(self, data: Dict[str, Any], max_attempts: int = 1) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Attempt to repair a JSON object so that it validates against the schema.
        Returns (repaired_data, applied_repairs, remaining_errors).
        Strategy:
          1. Run jsonschema validator. If no errors, return original.
          2. Apply heuristic_repair. Re-validate. If valid, return.
          3. (Optional) If self.llm provided, call LLM-based repair prompt to attempt better fixes.
          4. Return whatever we have (may still contain errors) along with logs.
        """
        applied_repairs_all: List[str] = []
        errors = validate_with_jsonschema(data)
        if not errors:
            return data, applied_repairs_all, []

        # Attempt heuristic repair
        repaired, applied = self.heuristic_repair(data)
        applied_repairs_all.extend(applied)

        # Validate again
        errors_after = validate_with_jsonschema(repaired)
        if not errors_after:
            return repaired, applied_repairs_all, []

        # If LLM client exists, attempt a single LLM repair (optional; fallback)
        if self.llm:
            prompt = self._build_repair_prompt(repaired, errors_after)
            # LLM expected to return JSON string only
            raw = self.llm.generate(prompt, temperature=0.0, max_tokens=1500)
            try:
                candidate = json.loads(raw)
                # Merge any _meta.repair_log entries
                if isinstance(candidate, dict):
                    candidate.setdefault("_meta", {})
                    candidate["_meta"].setdefault("from_llm", True)
                    candidate["_meta"]["llm_repaired_at"] = datetime.now(timezone.utc).isoformat()
                    applied_repairs_all.append("LLM repair attempted")
                    # Validate candidate
                    errors_candidate = validate_with_jsonschema(candidate)
                    if not errors_candidate:
                        return candidate, applied_repairs_all, []
                    else:
                        # return candidate plus remaining errors
                        return candidate, applied_repairs_all, errors_candidate
            except Exception:
                # LLM returned invalid JSON; treat as failure
                applied_repairs_all.append("LLM repair failed to produce valid JSON")
                return repaired, applied_repairs_all, errors_after

        # No LLM or LLM didn't help; return heuristic repaired plus remaining errors
        return repaired, applied_repairs_all, errors_after

    def _build_repair_prompt(self, json_obj: Dict[str, Any], errors: List[str]) -> str:
        """
        Build a short repair prompt (used if an LLM is provided).
        We'll include:
          - instruction to return only valid JSON matching schema
          - list of validator errors
          - the current JSON
        """
        summary_errors = "\n".join(f"- {e}" for e in errors[:20])
        ctx = json.dumps(json_obj, indent=2, ensure_ascii=False)
        prompt = (
            "REPAIR_JSON:\n"
            "You are a strict JSON repair agent. The following JSON failed schema validation for the Research Paper schema.\n"
            "Validator errors:\n"
            f"{summary_errors}\n\n"
            "Here is the current JSON (INPUT). Please return a repaired JSON object only, which satisfies the schema. "
            "Do NOT add commentary. If you need to fill missing values, use conservative placeholder tokens and add a top-level _meta.repair_log array describing your changes.\n\n"
            "INPUT JSON:\n"
            f"{ctx}\n\n"
            "OUTPUT:\n"
        )
        return prompt
