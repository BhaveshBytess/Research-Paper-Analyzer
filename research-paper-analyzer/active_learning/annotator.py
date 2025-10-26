# active_learning/annotator.py
"""
Annotator utilities: create CSV tasks for human labeling and ingest labeled CSVs.
"""

import csv
from typing import List, Dict, Iterable
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

ANNOTATION_COLS = ["item_id", "context_text", "suggested_label", "model_confidence", "label", "annotator", "annotated_at"]

def export_annotation_tasks(items: Iterable[Dict], out_csv: str, open_in_excel: bool = False) -> str:
    """
    items: iterable of dicts with keys: item_id, context_text, suggested_label (optional), model_confidence (optional)
    Writes a CSV with columns for human annotation and audit metadata.
    Returns path to CSV.
    """
    outp = Path(out_csv)
    rows = []
    for it in items:
        rows.append({
            "item_id": it.get("item_id"),
            "context_text": it.get("context_text") or "",
            "suggested_label": it.get("suggested_label") or "",
            "model_confidence": it.get("model_confidence") or "",
            "label": "",
            "annotator": "",
            "annotated_at": ""
        })
    df = pd.DataFrame(rows, columns=ANNOTATION_COLS)
    df.to_csv(outp, index=False, encoding="utf-8")
    # Optionally open in native app (not used in tests)
    if open_in_excel:
        try:
            import webbrowser
            webbrowser.open(str(outp.resolve()))
        except Exception:
            pass
    return str(outp.resolve())

def ingest_annotations(csv_path: str) -> List[Dict]:
    """
    Read annotated CSV and return list of dicts with item_id and label. Expects column 'label' filled in.
    Returns list of {"item_id":..., "label":..., "annotator":..., "annotated_at":...}
    """
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(csv_path)
    df = pd.read_csv(p, dtype=str).fillna("")
    out = []
    for _, row in df.iterrows():
        label = row.get("label", "").strip()
        if label == "":
            continue  # skip unannotated
        out.append({
            "item_id": row.get("item_id"),
            "label": label,
            "annotator": row.get("annotator", "") or "unknown",
            "annotated_at": row.get("annotated_at", "") or datetime.now(timezone.utc).isoformat()
        })
    return out
