# scripts/validate_summary.py
from rapidfuzz import fuzz
import json, sys

def sentence_matches_evidence(sentence, evidence_list, threshold=70):
    for ev in evidence_list:
        if fuzz.partial_ratio(sentence.lower(), ev.get("snippet","").lower()) >= threshold:
            return ev
    return None

def validate_summary(paper_path):
    paper = json.load(open(paper_path))
    summary = paper.get("summary", "")
    sentences = [s.strip() for s in summary.split('.') if s.strip()]
    evidence_flat = []
    for k in ["methods","results","title","limitations"]:
        for e in paper.get("evidence", {}).get(k, []):
            evidence_flat.append(e)
    matches = []
    for s in sentences:
        ev = sentence_matches_evidence(s, evidence_flat, threshold=65)
        matches.append((s, bool(ev), ev))
    # report
    for s, ok, ev in matches:
        print("SENT:", s[:120])
        print("  MATCHED:", ok, ("page", ev.get("page")) if ev else "")
    unmatched = [s for s,ok,_ in matches if not ok]
    print("Summary alignment:", (len(matches)-len(unmatched))/len(matches) if matches else 0.0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_summary.py path/to/paper.clean.json")
        sys.exit(1)
    validate_summary(sys.argv[1])
