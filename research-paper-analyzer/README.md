# Research Paper Analyzer

*Turn long research PDFs into grounded, structured JSON and an evidence-anchored summary—fast.*

![demo](assets/deepseek.mp4) <!-- Replace with actual GIF later -->

---

## Features

* Deterministic ≥0.9 **summary alignment** (no API required); LLM optional for polish
* Supports **Gemini** and **OpenRouter (DeepSeek)** backends, plus a **Mock** mode
* Clean **post-processing, confidence scoring, and sidecar metadata** for auditability

---

## Quickstart (90 seconds)

```bash
# 1) Create & activate venv
python -m venv venv
source venv/bin/activate       # Linux/Mac
.\venv\Scripts\activate        # Windows PowerShell

# 2) Install deps
pip install -r requirements.txt
pip install sentence-transformers rapidfuzz nltk
python -m nltk.downloader punkt

# 3) Configure keys (optional for LLMs)
# Create .env in repo root:
# GEMINI_API_KEY=your_key
# OPENROUTER_API_KEY=your_key

# 4) Run the app
streamlit run app/app.py
```

Or run the pipeline directly on a sample JSON:

```bash
# Post-process
python scripts/postprocess_paper.py examples/example_full.json

# Validate (semantic)
python scripts/validate_summary_semantic.py examples/example_full.clean.json

# Repair deterministically and re-validate
python scripts/repair_summary_anchor_semantic.py examples/example_full.clean.json examples/example_full.repaired.json
python scripts/validate_summary_semantic.py examples/example_full.repaired.json
```

Expected: alignment score ≥ 0.9 (sample reaches **1.0** after repair).

---

## What you get

* **Structured extraction**: metadata, methods, results, datasets/tasks, limitations, summary
* **Evidence for every claim**: `{ page, snippet }` collections preserved
* **Confidence**: per-result + aggregate (results mean)
* **Clean outputs**:

  * `paper.clean.json` — canonicalized, enriched
  * `paper.meta.json` — sidecar `_meta`
  * `paper.repaired.json` — summary anchored to evidence

---

## Example Metrics (sample run)

| Metric             | Value |
| ------------------ | ----- |
| JSON validity      | 98%   |
| Evidence precision | 92%   |
| Summary alignment  | 1.0   |

(Values vary by paper; reported for demo JSON)

---

## Architecture (file-wise)

* **Ingestion** — `ingestion/parser.py`: PDF → pages/text (born-digital; no OCR yet)
* **Evidence** — `evidence/locator.py`: find and store `{page, snippet}`
* **Orchestration** — `orchestrator/pipeline.py`, `orchestrator/heads.py` (+ `prompts/*.txt`):

  * Backends: Gemini, OpenRouter (DeepSeek), Mock
  * Heads: metadata, methods, results, summary
* **Schema** — `schema/*.py`, `schema/paper.schema.json`: Pydantic + JSON Schema
* **Post-process** — `scripts/postprocess_paper.py` + `results/compute_confidence.py`
* **Validate** — `scripts/validate_summary_semantic.py` (embeddings + fuzzy)
* **Repair** — `scripts/repair_summary_anchor_semantic.py` (deterministic ≥0.9)
* **UI** — `app/app.py` (Streamlit)
* **Examples** — `examples/*.json` (raw/clean/repaired)

📂 Flow: Parse → Extract (LLM) → Merge → Post-process → Validate → Repair → Validate → Serve.

---

## Configuration

* `.env` (optional if using Mock only)

  * `GEMINI_API_KEY` — Google Gemini
  * `OPENROUTER_API_KEY` — OpenRouter (e.g., `deepseek/deepseek-chat`)

Backend selection happens in the Streamlit UI or in `orchestrator/heads.py`.

---

## Deterministic summary alignment (why it matters)

We measure **summary-to-evidence grounding** per sentence.

* Semantic validator: `sentence-transformers` + cosine, with `rapidfuzz` fallback
* Repair strategy:

  * If sentence matches evidence strongly → keep + append `(see pX: "snippet...")`
  * If weak → replace with best evidence `(pX)`

Guarantees ≥0.9 alignment without LLMs; use LLM later for style.

---

## Troubleshooting

* **Activation**:

  * Linux/Mac → `source venv/bin/activate`
  * Windows → `.\venv\Scripts\activate`
* **Scanned PDFs**: OCR not enabled. Add Tesseract/pytesseract before ingestion.
* **Model download slow?** First run only; cached afterward.
* **Alignment low (<0.9)?** Ensure evidence exists → run repair script → adjust threshold (0.70) for paraphrases.

---

## 📂 Repo Map (selected)

* `app/app.py` — UI
* `ingestion/parser.py` — PDF parsing
* `orchestrator/*.py` — pipeline, heads, merge
* `prompts/*.txt` — head prompts
* `schema/*.py` — data models
* `scripts/*.py` — post-process, validate, repair
* `examples/*.json` — sample outputs

---

## Contributing

* Dev setup: create venv, install deps, run tests
* PRs welcome for:

  * new metrics
  * tasks/datasets lexicons
  * OCR integration
  * additional LLM backends

---

## License

MIT (see LICENSE)


