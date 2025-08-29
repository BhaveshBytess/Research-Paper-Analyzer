# tests/test_pipeline.py
from orchestrator.pipeline import Pipeline
from orchestrator.heads import HeadRunner
from schema.models import Paper

SAMPLE_CONTEXTS = {
    "metadata": "Hybrid Attention for Efficient Image Classification\nBhavesh Kumar, Jane Doe\nImaginaryConf 2023\narXiv:2301.00001",
    "methods": "We propose HybridAttentionNet: ConvStem + transformer blocks with MHA and RoPE. See Section 3.",
    "results": "Table 1: TinyImageNet test — HybridAttentionNet 78.4% vs ResNet18 75.0%.",
    "limitations": "Limitations: evaluation limited to small datasets. Ethics: no issues.",
    "summary": "Abstract: We introduce HybridAttentionNet ... Results: 78.4% on TinyImageNet ..."
}

def test_pipeline_runs_and_merges(tmp_path, monkeypatch):
    # Use HeadRunner with MockLLM (default)
    runner = HeadRunner()
    pipeline = Pipeline(head_runner=runner, cache_dir=str(tmp_path / ".cache"))
    merged = pipeline.run(SAMPLE_CONTEXTS)
    # Validate with Pydantic model
    paper = Paper(**merged)
    assert paper.title is not None
    assert isinstance(paper.authors, list)
    assert len(paper.results) >= 1
    # Ensure summary exists and limitations present
    assert paper.summary and len(paper.summary) > 10
    assert paper.limitations is not None
