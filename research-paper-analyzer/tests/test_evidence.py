# tests/test_evidence.py
from evidence.locator import attach_evidence_for_paper
from typing import List, Dict
import pytest

# Build synthetic pages like parser output
PAGES = [
    {
        "page_no": 1,
        "raw_text": "Hybrid Attention for Efficient Image Classification\nBhavesh Kumar, Jane Doe\nImaginaryConf 2023\narXiv:2301.00001",
        "clean_text": "Hybrid Attention for Efficient Image Classification Bhavesh Kumar, Jane Doe ImaginaryConf 2023 arXiv:2301.00001",
        "blocks": [
            {"bbox": [0,0,100,20], "text": "Hybrid Attention for Efficient Image Classification"},
            {"bbox": [0,30,200,60], "text": "Bhavesh Kumar, Jane Doe"},
            {"bbox": [0,60,200,90], "text": "ImaginaryConf 2023"}
        ]
    },
    {
        "page_no": 3,
        "raw_text": "We propose HybridAttentionNet which uses ConvStem and MHA with RoPE.",
        "clean_text": "We propose HybridAttentionNet which uses ConvStem and MHA with RoPE.",
        "blocks": [
            {"bbox":[0,0,200,20], "text": "We propose HybridAttentionNet which uses ConvStem and MHA with RoPE."}
        ]
    },
    {
        "page_no": 6,
        "raw_text": "Table 1: TinyImageNet test — HybridAttentionNet 78.4% vs ResNet18 75.0%.",
        "clean_text": "Table 1: TinyImageNet test — HybridAttentionNet 78.4% vs ResNet18 75.0%.",
        "blocks": [
            {"bbox":[0,0,300,40], "text":"Table 1: TinyImageNet test — HybridAttentionNet 78.4% vs ResNet18 75.0%."}
        ]
    }
]

# Synthetic merged paper
PAPER = {
    "title": "Hybrid Attention for Efficient Image Classification",
    "authors": ["Bhavesh Kumar","Jane Doe"],
    "year": 2023,
    "methods": [
        {"name": "HybridAttentionNet", "category": "Transformer+CNN", "components": ["ConvStem","MHA","RoPE"], "description": None}
    ],
    "results": [
        {"dataset": "TinyImageNet", "metric": "Accuracy", "value": 78.4, "unit": "%", "split": "test", "higher_is_better": True, "baseline": "ResNet18", "ours_is": "HybridAttentionNet", "confidence": 0.92}
    ],
    "limitations": "Evaluation limited to small datasets.",
    "summary": "We introduce HybridAttentionNet — a hybrid conv+transformer model that achieves 78.4% test accuracy on TinyImageNet."
}

def test_attach_evidence_basic():
    p, report = attach_evidence_for_paper(PAPER, PAGES, fuzzy_threshold=85.0, num_tolerance=0.5)
    # Evidence keys present
    assert "evidence" in p
    ev = p["evidence"]
    # title evidence found
    assert "title" in ev and len(ev["title"]) >= 1
    # methods evidence
    assert "methods" in ev and len(ev["methods"]) >= 1
    # results evidence
    assert "results" in ev and len(ev["results"]) >= 1
    # result snippet should contain numeric text
    assert any("78.4" in r["snippet"] or "78.4%" in r["snippet"] for r in ev["results"])
    # report indicates found items
    assert report["found"] >= 3

def test_numeric_tolerance_missing():
    # If target value slightly off beyond tolerance, should not match
    paper2 = dict(PAPER)
    paper2["results"] = [{"dataset":"TinyImageNet","metric":"Accuracy","value":85.0,"unit":"%"}]
    p2, rep2 = attach_evidence_for_paper(paper2, PAGES, fuzzy_threshold=85.0, num_tolerance=0.1)
    # Should not find the 85.0 value (no matches)
    assert rep2["details"]["results"] and rep2["details"]["results"][0] == False
