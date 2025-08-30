# results/compute_confidence.py
def compute_confidence_for_result(result: dict) -> float:
    # base scores
    src = result.get("_source", "").lower()
    snippet = (result.get("evidence_snippet") or "").lower()
    # provenance rules
    if src == "table":
        base = 0.95
    elif "%" in snippet or "bleu" in snippet:
        base = 0.9
    elif "table" in snippet or "table" in (result.get("evidence_snippet") or "").lower():
        base = 0.9
    elif src and "llm" in src:
        base = 0.75
    else:
        base = 0.7
    # bump if dataset present
    if result.get("dataset"):
        base += 0.03
    return round(min(base, 0.999), 3)
