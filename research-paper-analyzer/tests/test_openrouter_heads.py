# tests/test_deepseek_heads.py
import os
import pytest
from orchestrator.heads import HeadRunner, OpenRouterLLM

# These tests will be skipped if the OPENROUTER_API_KEY environment variable is not set.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SAMPLE_METHODS_CONTEXT = "We propose HybridAttentionNet: ConvStem + transformer blocks with MHA and RoPE. See Section 3."
SAMPLE_RESULTS_CONTEXT = "Table 1: TinyImageNet test — HybridAttentionNet 78.4% vs ResNet18 75.0%."
SAMPLE_METADATA_CONTEXT = "Hybrid Attention for Efficient Image Classification\nBhavesh Kumar, Jane Doe\nImaginaryConf 2023\narXiv:2301.00001"
SAMPLE_LIMITS_CONTEXT = "Limitations: evaluation limited to small datasets. Ethics: no issues."
SAMPLE_SUMMARY_CONTEXT = "Abstract: We introduce HybridAttentionNet ... Results: 78.4% on TinyImageNet ..."

@pytest.mark.skipif(not OPENROUTER_API_KEY, reason="OPENROUTER_API_KEY not set in environment")
def test_openrouter_metadata_head_parses():
    """
    This is an integration test that uses the real OpenRouter API for the metadata head.
    """
    llm_client = OpenRouterLLM()
    runner = HeadRunner(llm_client=llm_client)
    
    out = runner.run_metadata_head(SAMPLE_METADATA_CONTEXT)
    
    assert out.title is not None
    assert "Hybrid Attention" in out.title
    assert isinstance(out.authors, list)
    assert "Bhavesh Kumar" in out.authors
    assert out.year == 2023

@pytest.mark.skipif(not OPENROUTER_API_KEY, reason="OPENROUTER_API_KEY not set in environment")
def test_openrouter_methods_head_parses():
    """
    This is an integration test that uses the real OpenRouter API for the methods head.
    """
    llm_client = OpenRouterLLM()
    runner = HeadRunner(llm_client=llm_client)
    out = runner.run_methods_head(SAMPLE_METHODS_CONTEXT)
    assert isinstance(out.methods, list)
    assert len(out.methods) > 0
    assert out.methods[0].name == "HybridAttentionNet"

@pytest.mark.skipif(not OPENROUTER_API_KEY, reason="OPENROUTER_API_KEY not set in environment")
def test_openrouter_results_head_parses():
    """
    This is an integration test that uses the real OpenRouter API for the results head.
    """
    llm_client = OpenRouterLLM()
    runner = HeadRunner(llm_client=llm_client)
    out = runner.run_results_head(SAMPLE_RESULTS_CONTEXT)
    assert len(out.__root__) >= 1
    r = out.__root__[0]
    assert r.dataset == "TinyImageNet"
    assert r.metric.lower() == "accuracy"

@pytest.mark.skipif(not OPENROUTER_API_KEY, reason="OPENROUTER_API_KEY not set in environment")
def test_openrouter_limitations_head_parses():
    """
    This is an integration test that uses the real OpenRouter API for the limitations head.
    """
    llm_client = OpenRouterLLM()
    runner = HeadRunner(llm_client=llm_client)
    out = runner.run_limitations_head(SAMPLE_LIMITS_CONTEXT)
    assert "evaluation" in (out.limitations or "").lower()

@pytest.mark.skipif(not OPENROUTER_API_KEY, reason="OPENROUTER_API_KEY not set in environment")
def test_openrouter_summary_head_parses():
    """
    This is an integration test that uses the real OpenRouter API for the summary head.
    """
    llm_client = OpenRouterLLM()
    runner = HeadRunner(llm_client=llm_client)
    out = runner.run_summary_head(SAMPLE_SUMMARY_CONTEXT)
    assert len(out.summary) > 10
    assert "HybridAttentionNet" in out.summary
