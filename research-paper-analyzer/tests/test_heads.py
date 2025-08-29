# tests/test_heads.py
from orchestrator.heads import HeadRunner
from pathlib import Path

SAMPLE_METHODS_CONTEXT = "We propose HybridAttentionNet: ConvStem + transformer blocks with MHA and RoPE. See Section 3."
SAMPLE_RESULTS_CONTEXT = "Table 1: TinyImageNet test — HybridAttentionNet 78.4% vs ResNet18 75.0%."
SAMPLE_METADATA_CONTEXT = "Hybrid Attention for Efficient Image Classification\nBhavesh Kumar, Jane Doe\nImaginaryConf 2023\narXiv:2301.00001"
SAMPLE_LIMITS_CONTEXT = "Limitations: evaluation limited to small datasets. Ethics: no issues."
SAMPLE_SUMMARY_CONTEXT = "Abstract: We introduce HybridAttentionNet ... Results: 78.4% on TinyImageNet ..."

def test_metadata_head_parses():
    runner = HeadRunner()
    out = runner.run_metadata_head(SAMPLE_METADATA_CONTEXT)
    assert out.title is not None
    assert isinstance(out.authors, list)

def test_methods_head_parses():
    runner = HeadRunner()
    out = runner.run_methods_head(SAMPLE_METHODS_CONTEXT)
    assert isinstance(out.methods, list)
    assert out.methods[0].name == "HybridAttentionNet"

def test_results_head_parses():
    runner = HeadRunner()
    out = runner.run_results_head(SAMPLE_RESULTS_CONTEXT)
    assert len(out.__root__) >= 1
    r = out.__root__[0]
    assert r.dataset == "TinyImageNet"
    assert r.metric.lower() == "accuracy" or "acc" in r.metric.lower()

def test_limitations_head_parses():
    runner = HeadRunner()
    out = runner.run_limitations_head(SAMPLE_LIMITS_CONTEXT)
    assert "evaluation" in (out.limitations or "").lower()

def test_summary_head_parses():
    runner = HeadRunner()
    out = runner.run_summary_head(SAMPLE_SUMMARY_CONTEXT)
    assert len(out.summary) > 10
