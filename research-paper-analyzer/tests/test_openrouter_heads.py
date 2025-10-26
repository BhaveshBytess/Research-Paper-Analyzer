# tests/test_openrouter_heads.py
import json
import os
import pytest
from orchestrator.heads import HeadRunner, OpenRouterLLM

SAMPLE_METHODS_CONTEXT = "We propose HybridAttentionNet: ConvStem + transformer blocks with MHA and RoPE. See Section 3."
SAMPLE_RESULTS_CONTEXT = "Table 1: TinyImageNet test — HybridAttentionNet 78.4% vs ResNet18 75.0%."
SAMPLE_METADATA_CONTEXT = "Hybrid Attention for Efficient Image Classification\nBhavesh Kumar, Jane Doe\nImaginaryConf 2023\narXiv:2301.00001"
SAMPLE_LIMITS_CONTEXT = "Limitations: evaluation limited to small datasets. Ethics: no issues."
SAMPLE_SUMMARY_CONTEXT = "Abstract: We introduce HybridAttentionNet ... Results: 78.4% on TinyImageNet ..."

@pytest.fixture
def stubbed_openrouter(monkeypatch):
    """
    Provide an OpenRouterLLM instance whose network call is replaced with deterministic JSON.
    This keeps the tests offline-friendly while still exercising the HeadRunner wiring that
    expects an OpenRouterLLM-compatible client.
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", "test-openrouter-key"))

    def _fake_generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 256) -> str:
        if "Extract evaluation results" in prompt or '"dataset"' in prompt:
            return json.dumps([
                {
                    "dataset": "TinyImageNet",
                    "metric": "Accuracy",
                    "value": 78.4,
                    "unit": "%",
                    "split": "test",
                    "higher_is_better": True,
                    "baseline": "ResNet18",
                    "ours_is": "HybridAttentionNet",
                    "confidence": 0.92,
                }
            ])
        if "From the METHODS/ARCHITECTURE sections" in prompt or '"methods"' in prompt:
            return json.dumps({
                "methods": [
                    {
                        "name": "HybridAttentionNet",
                        "category": "Transformer+CNN",
                        "components": ["ConvStem", "MHA", "RoPE"],
                        "description": "ConvStem + light transformer blocks using RoPE.",
                    }
                ]
            })
        if "Extract the paper's limitations" in prompt or "limitations" in prompt:
            return json.dumps({
                "limitations": "Evaluation limited to small datasets.",
                "ethics": "No major ethical issues identified.",
            })
        if "Extract title" in prompt or '"title"' in prompt:
            return json.dumps({
                "title": "Hybrid Attention for Efficient Image Classification",
                "authors": ["Bhavesh Kumar", "Jane Doe"],
                "year": 2023,
                "venue": "ImaginaryConf",
                "arxiv_id": "arXiv:2301.00001",
            })
        if "concise summary" in prompt or '"summary"' in prompt:
            return json.dumps({
                "summary": "We introduce HybridAttentionNet — a hybrid conv+transformer model that achieves 78.4% test accuracy on TinyImageNet, outperforming ResNet18. Evaluation is limited to smaller datasets."
            })
        return "{}"

    monkeypatch.setattr(OpenRouterLLM, "generate", _fake_generate, raising=True)
    return OpenRouterLLM(api_key="test-openrouter-key", model_id="test/model")


def test_openrouter_metadata_head_parses(stubbed_openrouter):
    runner = HeadRunner(llm_client=stubbed_openrouter)
    
    out = runner.run_metadata_head(SAMPLE_METADATA_CONTEXT)
    
    assert out.title is not None
    assert "Hybrid Attention" in out.title
    assert isinstance(out.authors, list)
    assert "Bhavesh Kumar" in out.authors
    assert out.year == 2023


def test_openrouter_methods_head_parses(stubbed_openrouter):
    runner = HeadRunner(llm_client=stubbed_openrouter)
    out = runner.run_methods_head(SAMPLE_METHODS_CONTEXT)
    assert isinstance(out.methods, list)
    assert len(out.methods) > 0
    assert out.methods[0].name == "HybridAttentionNet"


def test_openrouter_results_head_parses(stubbed_openrouter):
    runner = HeadRunner(llm_client=stubbed_openrouter)
    out = runner.run_results_head(SAMPLE_RESULTS_CONTEXT)
    assert len(out.__root__) >= 1
    r = out.__root__[0]
    assert r.dataset == "TinyImageNet"
    assert r.metric.lower() == "accuracy"


def test_openrouter_limitations_head_parses(stubbed_openrouter):
    runner = HeadRunner(llm_client=stubbed_openrouter)
    out = runner.run_limitations_head(SAMPLE_LIMITS_CONTEXT)
    assert "evaluation" in (out.limitations or "").lower()


def test_openrouter_summary_head_parses(stubbed_openrouter):
    runner = HeadRunner(llm_client=stubbed_openrouter)
    out = runner.run_summary_head(SAMPLE_SUMMARY_CONTEXT)
    assert len(out.summary) > 10
    assert "HybridAttentionNet" in out.summary
