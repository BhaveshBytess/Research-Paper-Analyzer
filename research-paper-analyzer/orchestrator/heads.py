# orchestrator/heads.py
import json
from pathlib import Path
from typing import Any, Dict
from schema.head_models import MetadataOutput, MethodsOutput, ResultsOutput, LimitationsOutput, SummaryOutput

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

class MockLLM:
    """
    Deterministic mock LLM for offline dev/testing.
    Returns canned JSON for each head given a short context.
    """
    def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 512) -> str:
        # Very small heuristic to choose which head this is
        if "Extract evaluation results" in prompt or '"dataset"' in prompt:
            # return a simple results array
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
                    "confidence": 0.92
                }
            ])
        if "From the METHODS/ARCHITECTURE sections" in prompt or '"methods"' in prompt:
            return json.dumps({
                "methods": [
                    {
                        "name": "HybridAttentionNet",
                        "category": "Transformer+CNN",
                        "components": ["ConvStem","MHA","RoPE"],
                        "description": "ConvStem + light transformer blocks using RoPE."
                    }
                ]
            })
        if "Extract the paper's limitations" in prompt or "limitations" in prompt:
            return json.dumps({
                "limitations": "Evaluation limited to small datasets.",
                "ethics": "No major ethical issues identified."
            })
        if "Extract title" in prompt or '"title"' in prompt:
            return json.dumps({
                "title": "Hybrid Attention for Efficient Image Classification",
                "authors": ["Bhavesh Kumar", "Jane Doe"],
                "year": 2023,
                "venue": "ImaginaryConf",
                "arxiv_id": "arXiv:2301.00001"
            })
        if "concise summary" in prompt or '"summary"' in prompt:
            return json.dumps({
                "summary": "We introduce HybridAttentionNet — a hybrid conv+transformer model that achieves 78.4% test accuracy on TinyImageNet, outperforming ResNet18. Evaluation is limited to smaller datasets."
            })
        # default fallback: return empty JSON object
        return "{}"

class HeadRunner:
    def __init__(self, llm_client=None, temperature: float = 0.0):
        self.llm = llm_client or MockLLM()
        self.temperature = temperature

    def _load_prompt(self, head_name: str, context: str) -> str:
        p = PROMPTS_DIR / f"{head_name}_prompt.txt"
        if not p.exists():
            raise FileNotFoundError(f"Prompt template not found: {p}")
        template = p.read_text(encoding="utf-8")
        return template.replace("{context_text}", context)

    def run_metadata_head(self, context: str) -> MetadataOutput:
        prompt = self._load_prompt("metadata", context)
        raw = self.llm.generate(prompt, temperature=self.temperature)
        data = json.loads(raw)
        return MetadataOutput(**data)

    def run_methods_head(self, context: str) -> MethodsOutput:
        prompt = self._load_prompt("methods", context)
        raw = self.llm.generate(prompt, temperature=self.temperature)
        data = json.loads(raw)
        return MethodsOutput(**data)

    def run_results_head(self, context: str) -> ResultsOutput:
        prompt = self._load_prompt("results", context)
        raw = self.llm.generate(prompt, temperature=self.temperature)
        data = json.loads(raw)
        return ResultsOutput.parse_obj(data)

    def run_limitations_head(self, context: str) -> LimitationsOutput:
        prompt = self._load_prompt("limitations", context)
        raw = self.llm.generate(prompt, temperature=self.temperature)
        data = json.loads(raw)
        return LimitationsOutput(**data)

    def run_summary_head(self, context: str) -> SummaryOutput:
        prompt = self._load_prompt("summary", context)
        raw = self.llm.generate(prompt, temperature=self.temperature)
        data = json.loads(raw)
        return SummaryOutput(**data)
