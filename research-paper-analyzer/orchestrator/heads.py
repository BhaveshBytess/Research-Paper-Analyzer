# orchestrator/heads.py
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

from schema.head_models import (
    LimitationsOutput,
    MetadataOutput,
    MethodsOutput,
    ResultsOutput,
    SummaryOutput,
)

load_dotenv()

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class LLMGenerationError(RuntimeError):
    """Raised when an LLM backend fails to return usable content."""


class OpenRouterLLM:
    """Wrapper for the OpenRouter API (supports Grok, DeepSeek, etc.)."""

    DEFAULT_MODEL = "deepseek/deepseek-chat-v3.1:free"

    def __init__(self, api_key: Optional[str] = None, model_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not provided. Set OPENROUTER_API_KEY environment variable."
            )

        self.model_id = model_id or os.getenv("OPENROUTER_MODEL") or self.DEFAULT_MODEL
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=self.api_key)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> str:
        """Generate content using the configured OpenRouter model."""
        prompt = prompt[:3000]
        max_tokens = min(max_tokens, 256)

        try:
            completion = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": ("You are a strict JSON generator. Respond with JSON only. Do not include code fences, prose, or explanations.")},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            message = completion.choices[0].message
            cleaned_text = (message.content or "").strip()
            if not cleaned_text:
                reasoning = getattr(message, "reasoning", None)
                if reasoning:
                    cleaned_text = reasoning.strip()
            if not cleaned_text:
                reasoning_details = getattr(message, "reasoning_details", None) or []
                for detail in reasoning_details:
                    text = detail.get("text")
                    if text:
                        cleaned_text = text.strip()
                        if cleaned_text:
                            break
            if cleaned_text.lower().startswith("```json"):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]

            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            # Strip known sentinel tokens emitted by some models (DeepSeek)
            SENTINELS = {
                "<|begin_of_sentence|>",
                "<|end_of_sentence|>",
                "<|end_of_text|>",
                "<|fim_suffix|>",
                "<|fim_middle|>",
                "<|fim_prefix|>",
                "<\uff5cbegin\u2581of\u2581sentence\uff5c>",
                "<\uff5cend\u2581of\u2581sentence\uff5c>",
                "<\uff5cend\u2581of\u2581text\uff5c>",
            }
            for token in SENTINELS:
                if token in cleaned_text:
                    cleaned_text = cleaned_text.replace(token, " ")

            cleaned_text = cleaned_text.strip()

            return cleaned_text.strip()
        except Exception as exc:
            detail = str(exc)
            hint = ""
            if "No endpoints found matching your data policy" in detail:
                hint = (
                    " Update your OpenRouter privacy settings to allow the selected"
                    " model (https://openrouter.ai/settings/privacy) or pick a model"
                    " permitted by your account."
                )
            raise LLMGenerationError(
                f"OpenRouter call failed for model '{self.model_id}'. "
                "Verify OPENROUTER_API_KEY, OPENROUTER_MODEL, and quota."
                f"{hint} Details: {detail}"
            ) from exc

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
