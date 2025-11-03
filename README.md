# Research Paper Analyzer

**Automated extraction of structured data from scientific papers with evidence grounding and validation.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## Demo

![Demo](assets/deepseek.gif)

## Overview

Research Paper Analyzer transforms scientific PDFs into structured, machine-readable JSON with page-level evidence grounding. Built for researchers, ML engineers, and literature review automation, it extracts methods, results, datasets, and claims while maintaining traceability to source text.

**Key differentiator:** Evidence-grounded extraction with numeric consistency validation — not just LLM scraping.

```
PDF Input → Layout Analysis → LLM Extraction → Schema Validation → Evidence Linking → Structured JSON
```

---

## Why This Exists

### The Problem
- Manual paper analysis doesn't scale
- Existing tools extract text but lose structure
- LLM outputs are unreliable without validation
- No traceability from claims to source evidence

### This Solution
- ✅ **Structured extraction** with enforced schema
- ✅ **Evidence grounding** — every claim links to page + snippet
- ✅ **Numeric consistency checks** — catches hallucinated metrics
- ✅ **Model-agnostic** — works with DeepSeek, Gemma, Claude, GPT
- ✅ **Production-validated** — 100% success rate on 10 diverse papers

---

## Features

### Core Pipeline
- **PDF Parsing**: Multi-layout understanding (text, figures, tables, equations)
- **Context Building**: Semantic chunking for 5 extraction heads (metadata, methods, results, limitations, summary)
- **LLM Extraction**: Parallel extraction with automatic repair
- **Schema Enforcement**: Pydantic models + JSON schema validation
- **Evidence Attachment**: Fuzzy matching (85% threshold) with page references
- **Consistency Validation**: Range checks, baseline logic, unit verification

### Evaluation Metrics (Production-Validated)
| Metric | Score | Status |
|--------|-------|--------|
| **JSON Validity** | 100% | ✅ Schema compliance |
| **Evidence Precision** | 81% | ✅ Grounding quality |
| **Field Coverage** | 100% | ✅ Complete extraction |
| **Numeric Consistency** | 100% | ✅ Zero hallucinations |
| **Summary Alignment** | 58% | 🟡 Context matching |

*Benchmarked on 10 real papers (7-29 pages) including "Attention is All You Need"*

### User Interfaces
- **Streamlit Web UI**: Interactive upload, extraction, visualization
- **CLI Tool**: Batch processing with checkpoint/resume
- **Python API**: Programmatic access for pipelines

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                          │
│  PDF Upload → PyMuPDF Parser → Text + Layout Extraction     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     PROCESSING LAYER                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Metadata   │  │   Methods   │  │   Results   │        │
│  │  Extractor  │  │  Extractor  │  │  Extractor  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         ↓                 ↓                 ↓               │
│  ┌────────────────────────────────────────────────┐        │
│  │         LLM Backend (DeepSeek/Gemma)           │        │
│  └────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    VALIDATION LAYER                         │
│  JSON Repair → Schema Validation → Numeric Consistency      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     EVIDENCE LAYER                          │
│  Fuzzy Matching → Page Linking → Snippet Extraction         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                           │
│  Structured JSON + Evidence + Evaluation Metrics            │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/BhaveshBytess/research-paper-analyzer.git
cd research-paper-analyzer

# Create virtual environment (Python 3.10+)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key (OpenRouter for DeepSeek)
export OPENROUTER_API_KEY="your-key-here"
```

### Usage

**Web UI (Recommended)**
```bash
streamlit run research-paper-analyzer/app.py
```

**CLI (Single Paper)**
```bash
python run_now.py /path/to/paper.pdf
```

**CLI (Batch Processing)**
```bash
python batch_deepseek_inline.py
# Processes 2 papers at a time with auto-resume
# Results saved to batch_eval_results/
```

**Python API**
```python
from research_paper_analyzer import extract_paper

result = extract_paper(
    pdf_path="paper.pdf",
    model="deepseek",
    validate=True,
    attach_evidence=True
)

print(result.json(indent=2))
```

---

## Output Schema

### Core Fields

```json
{
  "title": "string",
  "authors": ["string"],
  "year": 2024,
  "venue": "string | null",
  "arxiv_id": "string | null",
  "methods": [
    {
      "name": "string",
      "category": "CNN | Transformer | GNN | ...",
      "components": ["string"],
      "description": "string"
    }
  ],
  "results": [
    {
      "dataset": "string",
      "metric": "string",
      "value": 0.95,
      "unit": "%" | "points" | null,
      "split": "test | val | train",
      "higher_is_better": true,
      "baseline": "string | null",
      "ours_is": "string | null",
      "confidence": 0.9
    }
  ],
  "tasks": ["string"],
  "datasets": ["string"],
  "limitations": "string | null",
  "ethics": "string | null",
  "summary": "string",
  "evidence": {
    "title": [{"page": 1, "snippet": "..."}],
    "methods": [{"page": 3, "snippet": "..."}],
    "results": [{"page": 7, "snippet": "..."}]
  }
}
```

### Validation Rules
- ✅ All numeric results must have valid `value` (not null)
- ✅ Percentages constrained to [0, 100]
- ✅ Confidence scores constrained to [0, 1]
- ✅ `higher_is_better` logic enforced vs. baseline
- ✅ Evidence keys must match extracted fields

---

## Benchmarks

### Performance (10 Papers, Mixed Domains)

| Metric | Target | Achieved | Notes |
|--------|--------|----------|-------|
| JSON Validity | 100% | **100%** | All outputs schema-compliant |
| Evidence Precision | ≥70% | **81%** | Grounding to source text |
| Field Coverage | 100% | **100%** | No missing required fields |
| Numeric Consistency | 100% | **100%** | Zero hallucinated metrics |
| Processing Speed | <2 min/paper | **~2 min** | On free-tier API |

### Test Set Details
- **Papers:** 10 (GNN methods, transformers, graph learning)
- **Page range:** 7-29 pages
- **Venues:** ICLR, NIPS, arXiv
- **Success rate:** 100% (10/10 papers extracted)
- **Perfect papers:** 2 (all metrics = 1.00)

**Landmark paper tested:** "Attention is All You Need" (Vaswani et al.) — successfully extracted all 8 authors, transformer components, and BLEU scores.

---

## Project Structure

```
research-paper-analyzer/
├── research-paper-analyzer/
│   ├── app.py                    # Streamlit UI
│   ├── pdf_parser.py             # PyMuPDF extraction
│   ├── llm_extractor.py          # LLM extraction logic
│   ├── schema.py                 # Pydantic models
│   ├── evidence_matcher.py       # Fuzzy evidence linking
│   └── eval_metrics.py           # Consistency validation
├── batch_deepseek_inline.py      # Batch evaluation script
├── create_visualizations.py      # Metric visualization
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── batch_eval_results/           # Evaluation results
│   ├── results.csv               # Metrics table
│   ├── visualizations/           # 8 analysis charts
│   └── summary/                  # Detailed reports
├── samples/                      # Test papers + results
└── datastore/                    # Cache + intermediate data
```

---

## Development

### Running Tests
```bash
# Unit tests (TODO: expand coverage)
pytest tests/

# Integration test on sample paper
python test_consistency.py
```

### Adding a New LLM Backend
1. Implement `BaseLLMExtractor` interface in `llm_extractor.py`
2. Add model config to `schema.py`
3. Update `run_now.py` with new model option

### Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code style (Black, isort)
- PR checklist
- Issue templates
- Architecture decisions

---

## Known Limitations

### Current Scope
- ❌ **No OCR support** — requires digital PDFs (not scanned images)
- ❌ **No figure extraction** — text-only for now
- ❌ **English papers only** — no multilingual support yet
- ⚠️ **Free-tier rate limits** — 16 req/min on OpenRouter (manageable for batch)

### Improvement Areas
- 🟡 **Summary alignment (58%)** — threshold tuning needed
- 🟡 **Complex table parsing** — nested tables occasionally missed
- 🟡 **Citation extraction** — not yet implemented

### Non-Issues
- ✅ **Numeric consistency** — validated at 100% (production-ready)
- ✅ **Schema compliance** — 100% across all tests
- ✅ **Evidence grounding** — 81% precision (excellent)

---

## Roadmap

### v1.1 (Current)
- [x] Core extraction pipeline
- [x] Evidence grounding
- [x] Numeric consistency validation
- [x] Batch evaluation system
- [x] Comprehensive benchmarks

### v1.2 (Next)
- [ ] OCR support (scanned PDFs)
- [ ] Figure caption extraction
- [ ] Citation graph parsing
- [ ] Multi-paper comparison UI
- [ ] Active learning for uncertain extractions

### v2.0 (Future)
- [ ] Multilingual support (non-English papers)
- [ ] Table structure extraction
- [ ] Equation parsing (LaTeX)
- [ ] Real-time collaboration (multi-user annotation)
- [ ] API service deployment (FastAPI + Docker)

---

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{research_paper_analyzer_2024,
  author = {Bhavesh Bytess},
  title = {Research Paper Analyzer: Evidence-Grounded PDF Extraction},
  year = {2024},
  url = {https://github.com/BhaveshBytess/research-paper-analyzer}
}
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **PyMuPDF** for robust PDF parsing
- **OpenRouter** for LLM API access
- **DeepSeek** for high-quality extraction
- **Streamlit** for rapid UI prototyping

---

## Contact & Support

- **Issues**: [GitHub Issues](https://github.com/BhaveshBytess/research-paper-analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/BhaveshBytess/research-paper-analyzer/discussions)
- **Email**: 10bhavesh7.11@gmail.com

**Maintained by:** [Bhavesh Bytess](https://github.com/BhaveshBytess)  
**Status:** Active development, production-validated, seeking contributors

---

## Quick Links

- 📊 [Batch Evaluation Results](batch_eval_results/INDEX.md)
- 📈 [Visualizations](batch_eval_results/visualizations/)
- 🧪 [Test Papers](samples/)
- 📝 [API Documentation](docs/API.md) *(coming soon)*
- 🎯 [Contribution Guide](CONTRIBUTING.md) *(coming soon)*

---

**Last Updated:** 2025-11-03  
**Version:** 1.1.0  
**Production Status:** ✅ Validated (100% success rate on 10 papers)
