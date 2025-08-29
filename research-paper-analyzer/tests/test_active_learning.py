# tests/test_active_learning.py
from active_learning.sampler import rank_items_by_uncertainty, select_top_k
from active_learning.annotator import export_annotation_tasks, ingest_annotations
import os
import csv
import tempfile
import json

def test_sampler_rank_and_select():
    items = [
        {"item_id": "a", "probs": [0.9, 0.1]},
        {"item_id": "b", "probs": [0.5, 0.5]},
        {"item_id": "c", "probs": [0.6, 0.4]}
    ]
    ranked = rank_items_by_uncertainty(items, method="least_confidence")
    # Most uncertain should be b (0.5), then c (0.4), then a (0.1)
    assert ranked[0][0] == "b"
    assert ranked[1][0] == "c"
    assert ranked[2][0] == "a"
    top1 = select_top_k(items, k=1, method="least_confidence")
    assert len(top1) == 1 and top1[0]["item_id"] == "b"

def test_annotator_export_and_ingest(tmp_path):
    items = [
        {"item_id":"i1","context_text":"abc","suggested_label":"METHOD","model_confidence":0.4},
        {"item_id":"i2","context_text":"def","suggested_label":"RESULT","model_confidence":0.8}
    ]
    out_csv = tmp_path / "tasks.csv"
    path = export_annotation_tasks(items, str(out_csv))
    assert os.path.exists(path)
    # Simulate annotator filling csv
    # Read and update
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    rows[0]["label"] = "METHOD"
    rows[0]["annotator"] = "tester"
    rows[0]["annotated_at"] = "2025-01-01T00:00:00Z"
    # write back
    with open(path, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    # ingest
    annotations = ingest_annotations(str(path))
    assert len(annotations) == 1
    assert annotations[0]["item_id"] == rows[0]["item_id"]
    assert annotations[0]["label"] == "METHOD"
