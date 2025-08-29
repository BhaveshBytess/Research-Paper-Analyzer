# tests/test_eval.py
import json
from pathlib import Path
from eval.eval_metrics import evaluate_pair, evidence_precision_for_paper, token_f1, numeric_metrics_for_paper

def test_token_f1_basic():
    g = "We introduce HybridAttentionNet achieving 78.4% on TinyImageNet."
    p = "HybridAttentionNet achieves 78.4% on TinyImageNet."
    f1 = token_f1(g, p)
    assert f1 > 0.5

def test_evidence_precision_and_numeric():
    gold = {
        "title": "Hybrid Attention for Efficient Image Classification",
        "summary": "We introduce HybridAttentionNet — ... 78.4% on TinyImageNet.",
        "results": [{"dataset":"TinyImageNet","metric":"Accuracy","value":78.4}],
        "evidence": {
            "results": [{"page":6,"snippet":"HybridAttentionNet achieves 78.4% test accuracy on TinyImageNet."}]
        }
    }
    # a predicted doc that has exact evidence and correct numeric
    pred_good = {
        "title": "Hybrid Attention for Efficient Image Classification",
        "summary": "HybridAttentionNet gets 78.4% on TinyImageNet.",
        "results": [{"dataset":"TinyImageNet","metric":"Accuracy","value":78.4}],
        "evidence": {
            "results": [{"page":6,"snippet":"HybridAttentionNet achieves 78.4% test accuracy on TinyImageNet."}]
        }
    }
    # a predicted doc with wrong numeric and no evidence
    pred_bad = {
        "title": "Hybrid Attention for Efficient Image Classification",
        "summary": "HybridAttentionNet gets 75.0% on TinyImageNet.",
        "results": [{"dataset":"TinyImageNet","metric":"Accuracy","value":75.0}],
        "evidence": {}
    }
    # Evaluate good
    m_good = evaluate_pair(gold, pred_good)
    assert m_good["evidence_precision"] == 1.0 or m_good["evidence_precision"] is None is False
    nm_good = numeric_metrics_for_paper(gold, pred_good)
    assert nm_good["num_matched"] >= 1
    assert nm_good["mae"] == 0.0

    # Evaluate bad
    m_bad = evaluate_pair(gold, pred_bad)
    nm_bad = numeric_metrics_for_paper(gold, pred_bad)
    assert nm_bad["mae"] == abs(75.0 - 78.4)
