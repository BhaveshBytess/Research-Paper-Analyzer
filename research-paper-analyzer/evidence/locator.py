# evidence/locator.py
from typing import List, Dict, Any, Optional, Tuple
import re
from pathlib import Path

# fuzzy matching: prefer rapidfuzz if available, else difflib
try:
    from rapidfuzz import fuzz
    _HAS_RAPIDFUZZ = True
except Exception:
    from difflib import SequenceMatcher
    _HAS_RAPIDFUZZ = False

# numeric extraction regex
_NUMBER_RE = re.compile(r"([+-]?\d+(?:\.\d+)?)")

def _fuzzy_score(a: str, b: str) -> float:
    """
    Return a 0..100 fuzzy score. Uses rapidfuzz.partial_ratio if available, else SequenceMatcher ratio * 100.
    """
    if not a or not b:
        return 0.0
    if _HAS_RAPIDFUZZ:
        try:
            return float(fuzz.partial_ratio(a, b))
        except Exception:
            return 0.0
    else:
        # fallback: sequence matcher on shorter/longer strings
        try:
            sm = SequenceMatcher(None, a, b)
            return float(sm.ratio() * 100.0)
        except Exception:
            return 0.0

def _extract_snippet_around(text: str, match_start: int, match_end: int, window: int = 120) -> str:
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    snippet = text[start:end].strip()
    # trim newlines and long whitespace
    snippet = re.sub(r"\s+", " ", snippet)
    return snippet

def find_exact_substring_block(block_text: str, query: str) -> Optional[Tuple[int,int]]:
    idx = block_text.lower().find(query.lower())
    if idx >= 0:
        return (idx, idx + len(query))
    return None

def find_number_matches_in_text(text: str) -> List[Tuple[float, int, int, str]]:
    """
    Return list of tuples (value as float, start_idx, end_idx, matched_text) for all numeric tokens found.
    """
    matches = []
    for m in _NUMBER_RE.finditer(text):
        tok = m.group(1)
        try:
            val = float(tok)
            matches.append((val, m.start(1), m.end(1), tok))
        except Exception:
            continue
    return matches

def find_numeric_in_pages(pages: List[Dict[str, Any]], target_value: float, unit: Optional[str] = None,
                          tolerance: float = 0.5) -> Optional[Dict[str, Any]]:
    """
    Search pages for numeric token equal to target_value (consider tolerance).
    If found, returns {page:int, snippet:str, matched_text:str}. Else None.
    """
    for p in pages:
        text = p.get("clean_text", "") or p.get("raw_text", "")
        if not text:
            continue
        # quick textual exact check: if unit present and target_value formatted exactly present
        if unit == "%":
            # look for e.g., '78.4%' or '78.4 %'
            if re.search(rf"{re.escape(str(target_value))}\s*%", text):
                m = re.search(rf"{re.escape(str(target_value))}\s*%", text)
                snippet = _extract_snippet_around(text, m.start(), m.end())
                return {"page": p.get("page_no"), "snippet": snippet, "matched_text": m.group(0)}
        # numeric tokens
        nums = find_number_matches_in_text(text)
        for val, s, e, tok in nums:
            if abs(val - target_value) <= tolerance:
                snippet = _extract_snippet_around(text, s, e)
                return {"page": p.get("page_no"), "snippet": snippet, "matched_text": tok}
    return None

def find_query_in_pages(pages: List[Dict[str, Any]], query: str, fuzzy_threshold: float = 85.0,
                        window: int = 120) -> Optional[Dict[str, Any]]:
    """
    Search page blocks for best match to query. Return the first confident match as {page, snippet, score}.
    Strategy:
      - Search blocks first (if available)
      - Exact substring match preferred
      - Then fuzzy match on block-level text
      - If nothing, try full page clean_text fuzzy
    """
    if not query:
        return None
    # Normalize query whitespace
    q = " ".join(query.split())

    best = None  # tuple(score, page_no, snippet)
    for p in pages:
        page_no = p.get("page_no")
        blocks = p.get("blocks", [])
        # If blocks exist, use them
        if blocks:
            for b in blocks:
                btext = b.get("text", "")
                if not btext:
                    continue
                # exact substring
                exact = find_exact_substring_block(btext, q)
                if exact:
                    s, e = exact
                    snippet = _extract_snippet_around(btext, s, e, window)
                    return {"page": page_no, "snippet": snippet, "score": 100.0, "matched_text": btext[s:e]}
                # fuzzy
                score = _fuzzy_score(q, btext)
                if score >= fuzzy_threshold:
                    snippet = _extract_snippet_around(btext, 0, min(len(btext), window*2), window)
                    return {"page": page_no, "snippet": snippet, "score": score, "matched_text": None}
                # track best
                if (best is None) or (score > best[0]):
                    best = (score, page_no, btext)
        # fallback to page-level
        page_text = p.get("clean_text", "") or p.get("raw_text", "")
        if page_text:
            exact = page_text.lower().find(q.lower())
            if exact >= 0:
                s = exact
                e = exact + len(q)
                snippet = _extract_snippet_around(page_text, s, e, window)
                return {"page": page_no, "snippet": snippet, "score": 100.0, "matched_text": page_text[s:e]}
            score = _fuzzy_score(q, page_text)
            if score >= fuzzy_threshold:
                snippet = _extract_snippet_around(page_text, 0, min(len(page_text), window*2), window)
                return {"page": page_no, "snippet": snippet, "score": score, "matched_text": None}
            if (best is None) or (score > best[0]):
                best = (score, page_no, page_text)
    # if no one reached threshold, return None (conservative)
    return None

def attach_evidence_for_paper(paper: Dict[str, Any], pages: List[Dict[str, Any]],
                              fuzzy_threshold: float = 85.0, num_tolerance: float = 0.5,
                              snippet_window: int = 120) -> Dict[str, Any]:
    """
    Attach evidence to the paper dict in-place and return (paper, report)
    report: {found:int, missing:int, details: { field:bool }}
    Evidence keys used: title, methods, results, limitations, summary
    """
    # Make sure paper has evidence structure
    paper = dict(paper)  # shallow copy
    evidence_map: Dict[str, List[Dict[str,Any]]] = paper.get("evidence", {}) or {}
    report = {"found": 0, "missing": 0, "details": {}}

    # 1) title
    title = paper.get("title")
    if title:
        res = find_query_in_pages(pages, title, fuzzy_threshold=fuzzy_threshold, window=snippet_window)
        if res:
            evidence_map.setdefault("title", []).append({"page": res["page"], "snippet": res["snippet"]})
            report["found"] += 1
            report["details"]["title"] = True
        else:
            report["missing"] += 1
            report["details"]["title"] = False

    # 2) methods
    methods = paper.get("methods", []) or []
    method_found_count = 0
    for mi, m in enumerate(methods):
        # try matching method name first
        name = m.get("name") if isinstance(m, dict) else getattr(m, "name", None)
        found_any = False
        if name:
            res = find_query_in_pages(pages, name, fuzzy_threshold=fuzzy_threshold, window=snippet_window)
            if res:
                evidence_map.setdefault("methods", []).append({"page": res["page"], "snippet": res["snippet"]})
                method_found_count += 1
                found_any = True
        # if not found, try components
        if not found_any:
            comps = m.get("components", []) if isinstance(m, dict) else getattr(m, "components", [])
            for comp in comps:
                res = find_query_in_pages(pages, comp, fuzzy_threshold=fuzzy_threshold, window=snippet_window)
                if res:
                    evidence_map.setdefault("methods", []).append({"page": res["page"], "snippet": res["snippet"]})
                    method_found_count += 1
                    found_any = True
                    break
        report["details"].setdefault("methods", []).append(found_any)
    if method_found_count > 0:
        report["found"] += method_found_count
    else:
        report["missing"] += max(1, len(methods))

    # 3) results: numeric matching preferred
    results = paper.get("results", []) or []
    results_found = 0
    for ri, r in enumerate(results):
        # r may be dict or Pydantic obj
        dataset = r.get("dataset") if isinstance(r, dict) else getattr(r, "dataset", None)
        metric = r.get("metric") if isinstance(r, dict) else getattr(r, "metric", None)
        value = r.get("value") if isinstance(r, dict) else getattr(r, "value", None)
        unit = r.get("unit") if isinstance(r, dict) else getattr(r, "unit", None)
        # Try numeric search first
        matched = False
        if value is not None:
            try:
                target_value = float(value)
                res_num = find_numeric_in_pages(pages, target_value, unit=unit, tolerance=num_tolerance)
                if res_num:
                    # store with reference to dataset/metric
                    evidence_map.setdefault("results", []).append({"page": res_num["page"], "snippet": res_num["snippet"]})
                    results_found += 1
                    matched = True
            except Exception:
                matched = False
        # If not numeric-found, try dataset+metric query
        if not matched:
            fallback_query = " ".join(filter(None, [str(dataset) if dataset else "", str(metric) if metric else ""]))
            if fallback_query.strip():
                resq = find_query_in_pages(pages, fallback_query, fuzzy_threshold=fuzzy_threshold, window=snippet_window)
                if resq:
                    evidence_map.setdefault("results", []).append({"page": resq["page"], "snippet": resq["snippet"]})
                    results_found += 1
                    matched = True
        report["details"].setdefault("results", []).append(matched)
    report["found"] += results_found
    report["missing"] += max(0, len(results) - results_found)

    # 4) limitations
    limitations_text = paper.get("limitations")
    if limitations_text:
        res = find_query_in_pages(pages, limitations_text, fuzzy_threshold=fuzzy_threshold, window=snippet_window)
        if res:
            evidence_map.setdefault("limitations", []).append({"page": res["page"], "snippet": res["snippet"]})
            report["found"] += 1
            report["details"]["limitations"] = True
        else:
            report["missing"] += 1
            report["details"]["limitations"] = False

    # 5) summary — try to find summary text in pages
    summary_text = paper.get("summary")
    if summary_text:
        res = find_query_in_pages(pages, summary_text[:200], fuzzy_threshold=fuzzy_threshold, window=snippet_window)
        if res:
            evidence_map.setdefault("summary", []).append({"page": res["page"], "snippet": res["snippet"]})
            report["found"] += 1
            report["details"]["summary"] = True
        else:
            report["missing"] += 1
            report["details"]["summary"] = False

    # merge with existing evidence (do not overwrite)
    merged_evidence = dict(evidence_map)
    # assign back
    paper["evidence"] = merged_evidence

    # Compute a simple evidence_precision: found / (found+missing) if any items were checked
    total_checked = report["found"] + report["missing"]
    evidence_precision = (report["found"] / total_checked) if total_checked > 0 else None
    report["evidence_precision"] = evidence_precision

    return paper, report
