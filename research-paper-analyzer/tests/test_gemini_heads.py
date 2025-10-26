# tests/test_gemini_heads.py
"""
Gemini integration was deprecated in favor of OpenRouter (Grok / DeepSeek) models.

We keep this placeholder test module so historical references continue to import,
but we skip the entire module during collection so the pytest suite reflects the
current integration surface area.
"""

import pytest

pytest.skip(
    "Gemini support removed — use OpenRouterLLM tests instead.",
    allow_module_level=True,
)
