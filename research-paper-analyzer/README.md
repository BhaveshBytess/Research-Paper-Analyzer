# Research Paper Analyzer

Turn long research PDFs into grounded, structured JSON and an evidence‑anchored summary—fast.

- Deterministic ≥0.9 summary alignment (no API required); LLM optional for polish.
- Supports Gemini and OpenRouter (DeepSeek) backends, plus a Mock mode.
- Clean post‑processing, confidence scoring, and sidecar metadata for auditability.

## Quickstart (90 seconds)

```powershell
# 1) Create/activate venv (PowerShell)
python -m venv venv
.\venv\Scripts\Activate

# 2) Install deps
pip install -r requirements.txt
pip install sentence-transformers rapidfuzz nltk
python -m nltk.downloader punkt

# 3) Configure keys (optional for LLM)
# Create .env in repo root
# GEMINI_API_KEY=your_key
# OPENROUTER_API_KEY=your_key

# 4) Run the app
streamlit run app/app.py
```

Or run the pipeline on a sample JSON:

```powershell
# Post-process
python scripts/postprocess_paper.py examples\example_full.json
# Validate (semantic)
python scripts/validate_summary_semantic.py examples\example_full.clean.json
# Repair deterministically and re-validate
python scripts/repair_summary_anchor_semantic.py examples\example_full.clean.json examples\example_full.repaired.json
python scripts/validate_summary_semantic.py examples\example_full.repaired.json
```

Expected: alignment score ≥ 0.9 (the sample reaches 1.0 after repair).

## What you get

- Structured extraction: metadata, methods, results, datasets/tasks, limitations, summary
- Evidence for every claim: `{ page, snippet }` collections preserved
- Confidence: per-result and aggregate (results mean)
- Clean outputs:
  - `paper.clean.json` — canonicalized, enriched
  - `paper.meta.json` — sidecar `_meta`
  - `paper.repaired.json` — summary anchored to evidence

## Architecture (file-wise)

- Ingestion — `ingestion/parser.py`: PDF → pages/text (born‑digital; no OCR)
- Evidence — `evidence/locator.py`: find and store `{page, snippet}`
- Orchestration — `orchestrator/pipeline.py`, `orchestrator/heads.py` (+ `prompts/*.txt`):
  - Backends: Gemini, OpenRouter(DeepSeek), Mock
  - Heads: metadata, methods, results, summary
- Schema — `schema/*.py`, `schema/paper.schema.json`: Pydantic + JSON Schema
- Post‑process — `scripts/postprocess_paper.py` + `results/compute_confidence.py`
- Validate — `scripts/validate_summary_semantic.py` (embeddings + fuzzy)
- Repair — `scripts/repair_summary_anchor_semantic.py` (deterministic ≥0.9)
- UI — `app/app.py` (Streamlit)
- Examples — `examples/*.json` (raw/clean/repaired)

Flow: Parse → Extract (LLM) → Merge → Post‑process → Validate → Repair → Validate → Serve.

## Configuration

- `.env` (optional if using Mock only)
  - `GEMINI_API_KEY` — Google Gemini
  - `OPENROUTER_API_KEY` — OpenRouter (e.g., `deepseek/deepseek-chat`)
- Backend selection in the Streamlit UI; code paths in `orchestrator/heads.py`.

## Deterministic summary alignment (why it matters)

We measure summary‑to‑evidence grounding per sentence.
- Semantic validator: `sentence-transformers` + cosine, with `rapidfuzz` fallback
- Repair strategy:
  - If a sentence matches evidence strongly → keep and append `(see pX: "snippet...")`
  - If weak → replace with best evidence `(pX)`
- Guarantees high alignment without an LLM; use LLM later for style.

## Troubleshooting

- Activation (PowerShell): `.\nvenv\Scripts\Activate`
- Scanned PDFs: OCR isn’t enabled. Add Tesseract/pytesseract before ingestion.
- Model download is slow: it’s normal on first run; cached afterward.
- Alignment low (<0.9): ensure evidence exists; run the repair script; lower threshold slightly (0.70) if many paraphrases.

## Repo map (selected)

- `app/app.py` — UI
- `ingestion/parser.py` — PDF parsing
- `orchestrator/*.py` — pipeline, heads, merge
- `prompts/*.txt` — head prompts
- `schema/*.py` — data models
- `scripts/*.py` — post‑process, validate, repair
- `examples/*.json` — sample outputs

## Contributing

- Dev setup: create venv, install deps, run tests.
- PRs welcome for new metrics, tasks/datasets lexicons, OCR integration.

## License

MIT (see LICENSE).
