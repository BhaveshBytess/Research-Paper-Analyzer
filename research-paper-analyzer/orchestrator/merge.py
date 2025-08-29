# orchestrator/merge.py
from typing import Dict, Any, List
from schema.head_models import MethodItem, ResultRecord
from schema.models import Paper
from pydantic import ValidationError

def merge_heads_to_paper(head_outputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic merge logic:
    - metadata head is authoritative for title/authors/year/venue/arxiv_id
    - methods head provides methods list (append)
    - results head provides numeric result records (append)
    - limitations head provides limitations/ethics
    - summary head provides summary
    - evidence: left empty (Stage 6 will populate). confidence: aggregated shallowly.
    """

    paper: Dict[str, Any] = {}
    # Metadata first (authoritative)
    metadata = head_outputs.get("metadata")
    if metadata:
        paper["title"] = getattr(metadata, "title", None)
        paper["authors"] = getattr(metadata, "authors", []) or []
        paper["year"] = getattr(metadata, "year", None)
        paper["venue"] = getattr(metadata, "venue", None)
        paper["arxiv_id"] = getattr(metadata, "arxiv_id", None)
    else:
        paper["title"] = None
        paper["authors"] = []
        paper["year"] = None

    # Methods
    methods_out = head_outputs.get("methods")
    if methods_out:
        # each MethodItem -> dict
        raw_methods = getattr(methods_out, "methods", [])
        methods_list: List[Dict[str, Any]] = [m.dict() if hasattr(m, 'dict') else m for m in raw_methods]
        paper["methods"] = methods_list
    else:
        paper["methods"] = []

    # Results
    results_out = head_outputs.get("results")
    if results_out:
        # ResultsOutput is a __root__ List[ResultRecord]
        try:
            raw_results = getattr(results_out, "__root__", [])
            results_list = [r.dict() if hasattr(r, 'dict') else r for r in raw_results]
        except Exception:
            results_list = []
        paper["results"] = results_list
    else:
        paper["results"] = []

    # Limitations & ethics
    limits_out = head_outputs.get("limitations")
    if limits_out:
        paper["limitations"] = getattr(limits_out, "limitations", None)
        paper["ethics"] = getattr(limits_out, "ethics", None)
    else:
        paper["limitations"] = None
        paper["ethics"] = None

    # Summary
    summary_out = head_outputs.get("summary")
    paper["summary"] = getattr(summary_out, "summary", "") if summary_out else ""

    # Small confidence map (aggregate): take available confidences from results if present
    confidence_map: Dict[str, float] = {}
    # metadata confidence: assume 1.0 for mock (or absent)
    confidence_map["metadata"] = 1.0
    if results_out:
        # average of result confidences if present
        vals = []
        for r in getattr(results_out, "__root__", []):
            c = getattr(r, "confidence", None)
            if isinstance(c, (int, float)):
                vals.append(float(c))
        if vals:
            confidence_map["results"] = sum(vals) / len(vals)
    else:
        confidence_map["results"] = None

    paper["confidence"] = confidence_map

    # Evidence is empty for now (Stage 6 will populate)
    paper["evidence"] = {}

    # Safe defaults for other optional fields
    paper.setdefault("tasks", [])
    paper.setdefault("datasets", [])
    paper.setdefault("ablations", [])
    paper.setdefault("open_source", None)
    paper.setdefault("novelty", None)

    # Validate against Pydantic Paper model; raise ValidationError if invalid
    try:
        Paper(**paper)
    except ValidationError as e:
        # Raise the same error for pipeline to handle / report
        raise

    return paper
