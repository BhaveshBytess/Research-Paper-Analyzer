# orchestrator/merge.py
from typing import Dict, Any, List
from datetime import datetime
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
        paper["authors"] = getattr(metadata, "authors", [])
        paper["year"] = getattr(metadata, "year", None)
        paper["venue"] = getattr(metadata, "venue", None)
        paper["arxiv_id"] = getattr(metadata, "arxiv_id", None)
    else:
        paper["title"] = None
        paper["authors"] = []
        paper["year"] = None

    # Methods
    methods_out = head_outputs.get("methods")
    raw_methods = []
    if methods_out:
        raw_methods = getattr(methods_out, "methods", []) or []
    paper["methods"] = [m.dict() if hasattr(m, 'dict') else m for m in raw_methods]

    # Results
    results_out = head_outputs.get("results")
    raw_results = []
    if results_out:
        # Handle case where __root__ could be None from a bad LLM parse
        raw_results = getattr(results_out, "__root__", []) or []
    
    paper["results"] = [r.dict() if hasattr(r, 'dict') else r for r in raw_results]

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
    paper["summary"] = getattr(summary_out, "summary", None) if summary_out else None

    repairs: List[str] = []
    if not paper.get("title"):
        paper["title"] = "Untitled (placeholder)"
        repairs.append("Inserted placeholder title because LLM returned none.")

    if not isinstance(paper.get("authors"), list):
        paper["authors"] = []
        repairs.append("Normalized authors list from invalid LLM output.")

    if paper.get("year") is None:
        paper["year"] = datetime.utcnow().year
        repairs.append("Filled missing year with current year placeholder.")

    if not paper.get("summary"):
        paper["summary"] = "Summary unavailable (placeholder)."
        repairs.append("Inserted placeholder summary because LLM returned none.")

    paper["authors"] = paper.get("authors") or []

    # Small confidence map (aggregate): take available confidences from results if present
    confidence_map: Dict[str, float] = {}
    # metadata confidence: assume 1.0 for mock (or absent)
    confidence_map["metadata"] = 1.0
    
    vals = []
    for r in raw_results:
        c = getattr(r, "confidence", None)
        if isinstance(c, (int, float)):
            vals.append(float(c))
    if vals:
        confidence_map["results"] = sum(vals) / len(vals)
    else:
        confidence_map["results"] = None

    paper["confidence"] = confidence_map

    if repairs:
        meta = paper.setdefault("_meta", {})
        repair_log = meta.setdefault("repair_log", [])
        repair_log.extend(repairs)

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
