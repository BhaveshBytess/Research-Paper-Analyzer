# eval/eval_metrics.py
import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from validation.schema_validator import validate_with_jsonschema
from store.store import load_paper, list_papers
from difflib import SequenceMatcher

# Try rapidfuzz for fuzzy matching if available
try:
    from rapidfuzz import fuzz
    _HAS_RAPIDFUZZ = True
except Exception:
    _HAS_RAPIDFUZZ = False

CORE_FIELDS = ["title", "authors", "year", "methods", "results", "summary", "evidence"]

def _fuzzy_score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if _HAS_RAPIDFUZZ:
        try:
            return float(fuzz.partial_ratio(a, b))
        except Exception:
            return 0.0
    else:
        return float(SequenceMatcher(None, a, b).ratio() * 100.0)

def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    # simple tokenization: words, numbers; lowercased
    tokens = re.findall(r"\w+", text.lower())
    return tokens

def token_f1(gold: str, pred: str) -> float:
    gold_toks = _tokenize(gold)
    pred_toks = _tokenize(pred)
    if not gold_toks and not pred_toks:
        return 1.0
    if not gold_toks or not pred_toks:
        return 0.0
    gold_set = {}
    for t in gold_toks:
        gold_set[t] = gold_set.get(t, 0) + 1
    common = 0
    pred_set = {}
    for t in pred_toks:
        pred_set[t] = pred_set.get(t, 0) + 1
    for t, cnt in pred_set.items():
        common += min(cnt, gold_set.get(t, 0))
    precision = common / len(pred_toks) if pred_toks else 0.0
    recall = common / len(gold_toks) if gold_toks else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)

def field_coverage(gold: Dict[str, Any], pred: Dict[str, Any]) -> float:
    present = 0
    for f in CORE_FIELDS:
        v = pred.get(f, None)
        if v is None:
            continue
        # consider non-empty lists/strings valid
        if isinstance(v, (list, dict)) and len(v) == 0:
            continue
        if isinstance(v, str) and v.strip() == "":
            continue
        present += 1
    return present / len(CORE_FIELDS)

def evidence_precision_for_paper(gold: Dict[str, Any], pred: Dict[str, Any], fuzzy_threshold: float = 85.0) -> Tuple[float, int, int]:
    """
    For each gold evidence item (across keys), check if an equivalent snippet exists in pred["evidence"].
    Returns (precision, matched_count, total_gold_evidence).
    """
    gold_evidence = gold.get("evidence", {}) or {}
    pred_evidence = pred.get("evidence", {}) or {}
    total = 0
    matched = 0
    for key, gold_items in gold_evidence.items():
        if not isinstance(gold_items, list):
            continue
        pred_items = pred_evidence.get(key, []) if pred_evidence else []
        for g in gold_items:
            total += 1
            g_snip = (g.get("snippet") or "").strip()
            found = False
            for p in pred_items:
                p_snip = (p.get("snippet") or "").strip()
                # exact substring test (case-insensitive)
                if g_snip and p_snip and (g_snip.lower() in p_snip.lower() or p_snip.lower() in g_snip.lower()):
                    found = True
                    break
                # fuzzy test
                score = _fuzzy_score(g_snip, p_snip)
                if score >= fuzzy_threshold:
                    found = True
                    break
            if found:
                matched += 1
    precision = (matched / total) if total > 0 else None
    return precision, matched, total

def numeric_consistency_check(paper: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check internal consistency of numeric results in a paper.
    Returns dict with consistency score and detailed checks.
    
    Checks performed:
    1. Baseline comparison logic (if higher_is_better=True, ours > baseline)
    2. Value range validation (percentages in [0,100], probabilities in [0,1])
    3. Unit consistency (same metric should have consistent units)
    4. Confidence score validity (must be in [0,1] if present)
    """
    results = paper.get("results", []) or []
    if not results:
        return {
            "consistency_score": None,
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": [],
            "notes": "No results to validate"
        }
    
    total_checks = 0
    passed = 0
    failed = []
    
    # Track units by metric for consistency checking
    metric_units = {}
    
    for idx, r in enumerate(results):
        if not isinstance(r, dict):
            continue
            
        value = r.get("value")
        unit = r.get("unit")
        metric = r.get("metric", "").lower().strip()
        baseline = r.get("baseline")
        ours_is = r.get("ours_is")
        higher_is_better = r.get("higher_is_better")
        confidence = r.get("confidence")
        
        # Check 1: Value must be numeric
        total_checks += 1
        try:
            value_float = float(value) if value is not None else None
            if value_float is None:
                failed.append(f"Result[{idx}]: value is None or missing")
            else:
                passed += 1
        except (ValueError, TypeError):
            failed.append(f"Result[{idx}]: value '{value}' is not numeric")
            continue
        
        # Check 2: Unit/value range consistency
        if unit and value_float is not None:
            total_checks += 1
            if unit == "%" or "percent" in metric:
                if 0 <= value_float <= 100:
                    passed += 1
                else:
                    failed.append(f"Result[{idx}]: percentage value {value_float} outside [0,100] range")
            elif "accuracy" in metric or "precision" in metric or "recall" in metric or "f1" in metric:
                # These could be % or decimal
                if unit == "%" and (0 <= value_float <= 100):
                    passed += 1
                elif unit != "%" and (0 <= value_float <= 1):
                    passed += 1
                elif 0 <= value_float <= 100:
                    passed += 1
                else:
                    failed.append(f"Result[{idx}]: metric '{metric}' value {value_float} outside expected range")
            else:
                passed += 1
        
        # Check 3: Confidence score validity
        if confidence is not None:
            total_checks += 1
            try:
                conf_float = float(confidence)
                if 0 <= conf_float <= 1:
                    passed += 1
                else:
                    failed.append(f"Result[{idx}]: confidence {conf_float} outside [0,1] range")
            except (ValueError, TypeError):
                failed.append(f"Result[{idx}]: confidence '{confidence}' is not numeric")
        
        # Check 4: Baseline comparison logic
        if baseline and ours_is and higher_is_better is not None and value_float is not None:
            # Find corresponding baseline value in results
            baseline_value = None
            for other in results:
                if not isinstance(other, dict):
                    continue
                other_name = other.get("ours_is") or other.get("baseline")
                if other_name and other_name.lower().strip() == baseline.lower().strip():
                    try:
                        baseline_value = float(other.get("value"))
                        break
                    except:
                        pass
            
            if baseline_value is not None:
                total_checks += 1
                if higher_is_better:
                    if value_float >= baseline_value:
                        passed += 1
                    else:
                        failed.append(f"Result[{idx}]: higher_is_better=True but ours ({value_float}) < baseline ({baseline_value})")
                else:
                    if value_float <= baseline_value:
                        passed += 1
                    else:
                        failed.append(f"Result[{idx}]: higher_is_better=False but ours ({value_float}) > baseline ({baseline_value})")
        
        # Check 5: Unit consistency tracking
        if metric:
            if metric not in metric_units:
                metric_units[metric] = []
            metric_units[metric].append((idx, unit))
    
    # Check unit consistency across same metrics
    for metric_name, unit_list in metric_units.items():
        if len(unit_list) > 1:
            units_seen = set(u for _, u in unit_list if u)
            if len(units_seen) > 1:
                total_checks += 1
                failed.append(f"Metric '{metric_name}' has inconsistent units: {units_seen}")
            elif len(units_seen) == 1:
                total_checks += 1
                passed += 1
    
    consistency_score = (passed / total_checks) if total_checks > 0 else None
    
    return {
        "consistency_score": consistency_score,
        "total_checks": total_checks,
        "passed_checks": passed,
        "failed_checks": failed,
        "notes": f"Validated {len(results)} results with {total_checks} consistency checks"
    }

def numeric_metrics_for_paper(gold: Dict[str, Any], pred: Dict[str, Any]) -> Dict[str, Any]:
    """
    For each gold result record, attempt to match a pred result by dataset+metric (case-insensitive exact or fuzzy).
    Returns dict containing lists of absolute errors and absolute percentage errors, and counts.
    """
    gold_results = gold.get("results", []) or []
    pred_results = pred.get("results", []) or []
    pred_index = []
    # normalize pred results into dict keyed by lowered dataset|metric
    for r in pred_results:
        ds = (r.get("dataset") or "").strip().lower()
        mt = (r.get("metric") or "").strip().lower()
        pred_index.append((ds, mt, r))
    abs_errors = []
    abs_perc_errors = []
    matched = 0
    for gr in gold_results:
        g_ds = (gr.get("dataset") or "").strip().lower()
        g_mt = (gr.get("metric") or "").strip().lower()
        g_val = gr.get("value")
        if g_val is None:
            continue
        # find best match in pred_index: prefer exact ds+mt match, else fuzzy metric match
        candidate = None
        for ds, mt, rr in pred_index:
            if ds == g_ds and mt == g_mt:
                candidate = rr
                break
        if candidate is None:
            # fuzzy match on dataset+metric combined
            best_score = -1.0
            for ds, mt, rr in pred_index:
                combined_gold = f"{g_ds} {g_mt}"
                combined_pred = f"{ds} {mt}"
                score = _fuzzy_score(combined_gold, combined_pred)
                if score > best_score:
                    best_score = score
                    candidate = rr
            # but only accept if >= threshold (say 80)
            if best_score < 80:
                candidate = None
        if candidate is None:
            continue
        p_val = candidate.get("value")
        try:
            g_val_f = float(g_val)
            p_val_f = float(p_val)
            abs_e = abs(p_val_f - g_val_f)
            abs_errors.append(abs_e)
            if g_val_f != 0:
                abs_perc_errors.append(abs_e / abs(g_val_f) * 100.0)
            matched += 1
        except Exception:
            continue
    result = {
        "num_gold_results": len(gold_results),
        "num_matched": matched,
        "mae": (sum(abs_errors)/len(abs_errors)) if abs_errors else None,
        "mape": (sum(abs_perc_errors)/len(abs_perc_errors)) if abs_perc_errors else None
    }
    return result

def evaluate_pair(gold: Dict[str, Any], pred: Dict[str, Any], fuzzy_threshold: float = 85.0) -> Dict[str, Any]:
    """
    Evaluate a single gold/pred pair and return metrics.
    """
    metrics = {}
    # JSON validity of pred (schema)
    errors = validate_with_jsonschema(pred)
    metrics["valid_json"] = (len(errors) == 0)
    metrics["json_errors"] = errors

    # field coverage
    metrics["field_coverage"] = field_coverage(gold, pred)

    # evidence precision
    precision, matched, total = evidence_precision_for_paper(gold, pred, fuzzy_threshold=fuzzy_threshold)
    metrics["evidence_precision"] = precision
    metrics["evidence_matched"] = matched
    metrics["evidence_total"] = total

    # numeric metrics
    nm = numeric_metrics_for_paper(gold, pred)
    metrics.update(nm)
    
    # numeric consistency check (self-evaluation)
    consistency = numeric_consistency_check(pred)
    metrics["numeric_consistency"] = consistency.get("consistency_score")
    metrics["numeric_consistency_details"] = consistency

    # summary token F1
    metrics["summary_f1"] = token_f1(gold.get("summary") or "", pred.get("summary") or "")

    return metrics

def evaluate_goldset(gold_dir: str, pred_dir: str, fuzzy_threshold: float = 85.0) -> Dict[str, Any]:
    """
    Load gold files from gold_dir and matching pred files from pred_dir (matching basenames),
    compute per-paper metrics and aggregates, and write report JSON into pred_dir/eval_report.json
    """
    gold_dir = Path(gold_dir)
    pred_dir = Path(pred_dir)
    report = {"per_paper": {}, "aggregates": {}}
    valid_count = 0
    fc_list = []
    ep_list = []
    summary_f1s = []
    mae_list = []
    mape_list = []
    total_gold = 0
    files = sorted([p for p in gold_dir.glob("*.json")])
    for gpath in files:
        base = gpath.name
        ppath = pred_dir / base
        if not ppath.exists():
            # skip or mark as missing
            report["per_paper"][base] = {"error": "prediction_missing"}
            continue
        gold = json.loads(open(gpath, "r", encoding="utf-8").read())
        pred = json.loads(open(ppath, "r", encoding="utf-8").read())
        metrics = evaluate_pair(gold, pred, fuzzy_threshold=fuzzy_threshold)
        report["per_paper"][base] = metrics
        # accumulate
        if metrics.get("valid_json"):
            valid_count += 1
        if metrics.get("field_coverage") is not None:
            fc_list.append(metrics["field_coverage"])
        if metrics.get("evidence_precision") is not None:
            ep_list.append(metrics["evidence_precision"])
        if metrics.get("summary_f1") is not None:
            summary_f1s.append(metrics["summary_f1"])
        if metrics.get("mae") is not None:
            mae_list.append(metrics["mae"])
        if metrics.get("mape") is not None:
            mape_list.append(metrics["mape"])
        total_gold += 1

    # aggregates
    aggregates = {}
    aggregates["valid_json_rate"] = (valid_count / total_gold) if total_gold else None
    aggregates["mean_field_coverage"] = (sum(fc_list)/len(fc_list)) if fc_list else None
    aggregates["mean_evidence_precision"] = (sum(ep_list)/len(ep_list)) if ep_list else None
    aggregates["mean_summary_f1"] = (sum(summary_f1s)/len(summary_f1s)) if summary_f1s else None
    aggregates["mean_mae"] = (sum(mae_list)/len(mae_list)) if mae_list else None
    aggregates["mean_mape"] = (sum(mape_list)/len(mape_list)) if mape_list else None
    report["aggregates"] = aggregates

    # write report to pred_dir for convenience
    out_path = pred_dir / "eval_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report

# Ablation helper
def compare_experiments(report_a: Dict[str, Any], report_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given two eval_report dictionaries (the outputs of evaluate_goldset),
    compute differences for key aggregates and return a small diff summary.
    """
    aagg = report_a.get("aggregates", {})
    bagg = report_b.get("aggregates", {})
    keys = set(list(aagg.keys()) + list(bagg.keys()))
    diffs = {}
    for k in keys:
        a_val = aagg.get(k)
        b_val = bagg.get(k)
        try:
            diff = None
            if a_val is not None and b_val is not None:
                diff = b_val - a_val
            diffs[k] = {"a": a_val, "b": b_val, "diff": diff}
        except Exception:
            diffs[k] = {"a": a_val, "b": b_val, "diff": None}
    return diffs

# CLI convenience
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate system outputs against a goldset")
    parser.add_argument("--gold_dir", required=True, help="path to eval/gold")
    parser.add_argument("--pred_dir", required=True, help="path to directory containing system outputs matching gold filenames")
    parser.add_argument("--fuzzy", type=float, default=85.0, help="fuzzy threshold for evidence matching (0-100)")
    args = parser.parse_args()
    rep = evaluate_goldset(args.gold_dir, args.pred_dir, fuzzy_threshold=args.fuzzy)
    print("Evaluation complete. Report saved to pred_dir/eval_report.json")
