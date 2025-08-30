# scripts/postprocess_paper.py
import json, sys, os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from results.compute_confidence import compute_confidence_for_result

def canonicalize_paper(paper: dict):
    # 1) Ensure numeric result values are floats and units normalized
    for r in paper.get("results", []):
        # numeric
        if r.get("value") is not None:
            try:
                r["value"] = float(r["value"])
            except:
                # leave as-is but flag
                r["_value_parsed"] = False
        # normalize BLEU unit
        if r.get("metric","").lower() == "bleu":
            r["unit"] = r.get("unit") or "BLEU"
        # ensure higher_is_better boolean
        if "higher_is_better" not in r:
            r["higher_is_better"] = True

    # 2) Fill confidence defaults container if null
    conf = paper.get("confidence", {})
    if conf is None: conf = {}
    conf["metadata"] = float(conf.get("metadata", 0.0))
    for r in paper.get("results", []):
        if r.get("confidence") is None:
            r["confidence"] = compute_confidence_for_result(r)
    # Then set overall confidence.results e.g. mean of per-result confidences
    vals = [r["confidence"] for r in paper.get("results",[]) if r.get("confidence") is not None]
    conf["results"] = round(sum(vals)/len(vals),3) if vals else 0.0
    paper["confidence"] = conf

    # 3) Derive datasets from results if datasets[] empty
    if not paper.get("datasets"):
        datasets = []
        for r in paper.get("results", []):
            ds = r.get("dataset")
            if ds and not any(d.get("name")==ds for d in datasets):
                datasets.append({"name": ds, "evidence": {"page": r.get("evidence_page"), "snippet": r.get("evidence_snippet")}})
        paper["datasets"] = datasets

    # 4) Derive tasks from methods if empty
    if not paper.get("tasks"):
        tasks = set()
        for m in paper.get("methods", []):
            name = m.get("name") or ""
            # naive mapping; expand lexicon as needed
            if "translation" in (m.get("description","").lower() + name.lower()):
                tasks.add("Machine Translation")
            if "object" in (m.get("description","").lower() + name.lower()):
                tasks.add("Object Detection")
            if "planning" in (m.get("description","").lower() + name.lower()):
                tasks.add("Motion Planning")
        paper["tasks"] = list(tasks)

    # 5) Paper type heuristic
    if paper.get("results"):
        # empirical if there are numeric results
        has_numeric = any(r.get("value") is not None for r in paper.get("results", []))
        paper["paper_type"] = "empirical" if has_numeric else "review"
    else:
        paper["paper_type"] = "review"

    return paper

def export_clean(paper_json_path):
    p = Path(paper_json_path)
    paper = json.loads(p.read_text(encoding="utf-8"))
    meta = paper.pop("_meta", None)  # remove _meta from main output
    paper = canonicalize_paper(paper)
    # name outputs
    out_clean = p.with_name(p.stem + ".clean.json")
    out_meta = p.with_name(p.stem + ".meta.json")
    out_clean.write_text(json.dumps(paper, ensure_ascii=False, indent=2))
    out_meta.write_text(json.dumps(meta or {}, ensure_ascii=False, indent=2))
    print("Wrote:", out_clean, "and sidecar meta:", out_meta)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python postprocess_paper.py path/to/paper.json")
        sys.exit(1)
    export_clean(sys.argv[1])
