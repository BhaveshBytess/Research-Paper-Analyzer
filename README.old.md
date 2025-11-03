#
# New README content below replaces and consolidates outdated sections
#

# Research Paper Analyzer

Convert research PDFs into structured JSON with evidence-backed summaries. Runs locally (offline mock) or with OpenRouter models. The Streamlit app preselects DeepSeek by default; Gemma via OpenRouter is supported with provider-safe fallbacks.

![demo](assets/deepseek.gif)

## Overview

This project parses a PDF into pages, extracts task-specific fields using prompt-driven heads (metadata, methods, results, limitations, summary), merges and repairs the output to match a schema, attaches page-level evidence snippets, and presents everything in a Streamlit UI. You can save validated JSON to a local datastore for later viewing.

Core pipeline:
- Parse PDF → pages/text (no OCR yet)
- Build lightweight contexts → run heads via LLM or offline mock
- Merge → repair → attach evidence → validate JSON schema
- View in UI, download JSON, or save to local datastore

## Features

- Streamlit UI with file upload and evidence visualization
- Head-based extraction: metadata, methods, results, limitations, summary
- Evidence attachment per section with page/snippet references
- Automatic structure repair and schema validation (jsonschema + Pydantic)
- Local datastore for saving and browsing processed papers
- LLM backends via OpenRouter: DeepSeek (default) and Google Gemma (with safe fallbacks)
- Offline “MockLLM” mode for quick demos and development without any API key

## Tech stack

- Python 3.10+
- Streamlit, Pydantic, jsonschema
- PDF parsing: PyMuPDF (pymupdf), pdfplumber
- Matching/heuristics: rapidfuzz, numpy, pandas, scikit-learn (light use)
- Optional CLI validators/repairs: sentence-transformers, NLTK

See full pinned versions in `research-paper-analyzer/requirements.txt`.

## Installation

Windows PowerShell (recommended):

```powershell
# 1) Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate

# 2) Install dependencies
pip install -r research-paper-analyzer/requirements.txt

# 3) (Optional) Extra packages for CLI semantic validators/repairs
pip install sentence-transformers
```

## Configuration

Copy `.env.example` to `.env` in the repository root if you plan to use OpenRouter models:

```dotenv
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_DEEPSEEK_MODEL=deepseek/deepseek-chat-v3.1:free
OPENROUTER_MODEL=google/gemma-3n-e4b-it:free
```

Notes:
- The UI preselects DeepSeek (OpenRouter). Offline mode works without any keys.
- Google Gemma via OpenRouter may restrict system/developer instructions and JSON mode; the app includes fallbacks to comply automatically.

## Usage

Run the Streamlit app from the repository root:

```powershell
python -m streamlit run research-paper-analyzer/app/app.py
```

Then open the printed Local URL (for example, http://localhost:8501 or http://localhost:8502).

In the app:
- Choose LLM mode: Offline, DeepSeek (OpenRouter), or Gemma (OpenRouter)
- Upload a PDF (e.g., `sample.pdf` in the root, or any file)
- Click “Process Paper” to generate and view: summary, repairs, evidence, results table, and full JSON
- Optionally save to local datastore and reload saved items from the sidebar

## CLI examples (optional)

These utilities live under `research-paper-analyzer/scripts` and require `sentence-transformers` (see Installation step 3).

```powershell
# Evaluate summary vs evidence (prints alignment score)
python research-paper-analyzer/scripts/validate_summary_semantic.py research-paper-analyzer/examples/example_full.clean.json

# Repair a summary by anchoring to evidence
python research-paper-analyzer/scripts/repair_summary_anchor_semantic.py research-paper-analyzer/examples/example_full.clean.json research-paper-analyzer/examples/example_full.repaired.json

# Batch evaluation across a folder of PDFs
python research-paper-analyzer/scripts/batch_eval.py research-paper-analyzer/pdfs --output research-paper-analyzer/results/batch_eval
```

## Project layout

```
assets/                       # demo assets (gif)
research-paper-analyzer/
  app/app.py                  # Streamlit UI
  ingestion/parser.py         # PDF → pages/text
  orchestrator/               # heads, pipeline, merge, repair
  evidence/locator.py         # evidence finding/attachment
  schema/                     # Pydantic models + JSON schema
  scripts/                    # CLI tools (validation/repair/batch eval)
  results/                    # evaluation outputs
  prompts/                    # prompt templates per head
  datastore/                  # local saved papers (ignored by git)
```

## Troubleshooting

- App won’t start: ensure packages are installed into the active virtualenv; try re-running the install step.
- Gemma 400 errors: provider limitations on developer instructions or JSON mode. The app now auto-avoids system messages and JSON mode for Gemma via OpenRouter.
- Scanned PDFs: OCR isn’t included; only text-layer PDFs are supported.
- Cached results: uncheck “Clear cache before running” to reuse cached head outputs.

## License

MIT — see `research-paper-analyzer/LICENSE` for full terms.

## Contributing

Issues and PRs are welcome. For larger changes (e.g., OCR integration, new heads, or additional LLM providers), please open an issue to discuss scope and design first.
* **Model download slow?** First run only; cached afterward.

* **Alignment low (<0.9)?** Ensure evidence exists → run repair script → adjust threshold (0.70) for paraphrases.

