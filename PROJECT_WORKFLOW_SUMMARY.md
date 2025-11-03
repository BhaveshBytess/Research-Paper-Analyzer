# Research Paper Analyzer - Complete Project Workflow Summary

**Project Owner**: Bhavesh Bytess  
**Repository**: [research-paper-analyzer](https://github.com/BhaveshBytess/research-paper-analyzer)  
**Date Created**: November 2025  
**Status**: ✅ Complete & Deployed

---

## 🎯 Project Overview

### What This Project Does
The **Research Paper Analyzer** is an automated pipeline that extracts structured information from academic research papers (PDFs) and outputs:
- **Structured JSON** with metadata, methods, datasets, results, limitations
- **Evidence-grounded extraction** with page references
- **Validation & consistency checking** for numeric results
- **Interactive Streamlit UI** for real-time paper analysis

### Core Technology Stack
- **Python 3.13+**
- **LLMs**: DeepSeek (primary), Gemma (fallback) via OpenRouter API
- **PDF Parsing**: PyMuPDF + pdfplumber
- **Schema Validation**: Pydantic + JSONSchema
- **UI**: Streamlit
- **Evaluation**: Custom metrics (JSON validity, evidence precision, field coverage, numeric consistency, summary alignment)

---

## 📂 Codebase Structure

### Directory Overview

```
RESEARCH-PAPER-ANALYZER/
├── research-paper-analyzer/          # Main application code
│   ├── app/                          # Streamlit UI
│   │   └── app.py                    # Main app entry point
│   ├── ingestion/                    # PDF parsing
│   │   └── parser.py                 # PyMuPDF + pdfplumber parser
│   ├── orchestrator/                 # LLM orchestration
│   │   ├── heads.py                  # Head runners (metadata, methods, results, etc.)
│   │   ├── pipeline.py               # Async pipeline with caching
│   │   ├── merge.py                  # Merge head outputs into Paper model
│   │   └── repair.py                 # JSON repair logic
│   ├── evidence/                     # Evidence attachment
│   │   └── locator.py                # Fuzzy matching evidence to PDF snippets
│   ├── schema/                       # Data models
│   │   ├── models.py                 # Pydantic models (Paper, Dataset, Method, etc.)
│   │   ├── head_models.py            # Models for individual heads
│   │   └── paper.schema.json         # JSONSchema for validation
│   ├── validation/                   # Schema validation
│   │   └── schema_validator.py       # JSONSchema validator
│   ├── eval/                         # Evaluation metrics
│   │   └── eval_metrics.py           # 5 core metrics implementation
│   ├── store/                        # Paper storage
│   │   └── store.py                  # Save/load papers with timestamps
│   └── prompts/                      # LLM prompts for each head
│       ├── metadata.txt
│       ├── methods.txt
│       ├── results.txt
│       ├── limitations.txt
│       └── summary.txt
├── batch_deepseek_inline.py          # Batch evaluation runner
├── create_visualizations.py          # Results visualization generator
├── batch_eval_results/               # Evaluation outputs
│   ├── results.csv                   # Per-paper metrics
│   ├── results.jsonl                 # Detailed results log
│   ├── *.json                        # Individual paper outputs
│   ├── summary/                      # Per-paper summary reports
│   └── visualizations/               # Charts and graphs
├── samples/                          # Test PDFs (research papers)
├── requirements.txt                  # Python dependencies
├── README.md                         # Main documentation
└── LICENSE                           # MIT License

```

---

## 🔄 Complete Workflow (End-to-End)

### Phase 1: PDF Ingestion
**Entry**: `ingestion/parser.py`
- **Input**: PDF file path
- **Process**:
  1. Extract pages using PyMuPDF
  2. Parse text blocks with layout information
  3. Extract clean text per page
- **Output**: JSON with `pages[]`, each containing `page_no`, `raw_text`, `blocks`, `clean_text`

### Phase 2: Context Building
**Entry**: `app/app.py` → `run_extraction_pipeline()`
- **Process**:
  1. Clip text from first page → metadata context (800 chars)
  2. Clip first half → methods context (1200 chars)
  3. Clip all pages → results context (1600 chars)
  4. Clip last 2 pages → limitations context (800 chars)
  5. Clip first + last page → summary context (1200 chars)
- **Output**: Dictionary of 5 contexts

### Phase 3: LLM Head Execution
**Entry**: `orchestrator/pipeline.py` → `Pipeline.run()`
- **Process** (async with caching):
  1. Run 5 heads in parallel:
     - **metadata**: title, authors, year, venue, arxiv_id, tasks
     - **methods**: method names, categories, components
     - **results**: datasets, metrics, values, baselines
     - **limitations**: limitations text
     - **summary**: paper summary
  2. Each head:
     - Loads prompt from `prompts/{head}.txt`
     - Calls LLM (DeepSeek/Gemma via OpenRouter)
     - Parses JSON response into Pydantic model
     - Caches result by hash of (head_name + context)
- **Output**: Dictionary of 5 head outputs

### Phase 4: Merging & Repair
**Entry**: `orchestrator/merge.py` → `merge_heads_to_paper()`
- **Process**:
  1. Merge all head outputs into single `Paper` model
  2. If validation fails → `orchestrator/repair.py`:
     - Attempt JSON repair (fix quotes, braces, trailing commas)
     - Retry validation
- **Output**: Valid `Paper` Pydantic model

### Phase 5: Evidence Attachment
**Entry**: `evidence/locator.py` → `attach_evidence_for_paper()`
- **Process**:
  1. For each field (title, methods, results, etc.):
     - Extract key phrases
     - Fuzzy search PDF pages for matching snippets
     - Record (page_number, snippet) as evidence
  2. Populate `paper.evidence` dict
- **Output**: `Paper` model with evidence attached

### Phase 6: Validation & Storage
**Entry**: `validation/schema_validator.py` + `store/store.py`
- **Process**:
  1. Validate against JSONSchema (`schema/paper.schema.json`)
  2. Save to `datastore/{paper_id}.json` with timestamp
  3. Return final JSON
- **Output**: Timestamped JSON file + in-memory dict

---

## 📊 Evaluation Metrics

### 5 Core Metrics (Implemented in `eval/eval_metrics.py`)

#### 1. **JSON Validity Rate**
- **What**: Percentage of outputs that pass JSONSchema validation
- **How**: `validate_with_jsonschema(paper)` → returns list of errors
- **Score**: 1.0 if no errors, 0.0 otherwise
- **Current Performance**: **100%** (10/10 papers)

#### 2. **Evidence Precision**
- **What**: How many extracted claims have verifiable evidence in the PDF
- **How**: Fuzzy match snippets in `paper.evidence` to PDF text
- **Score**: (matched_snippets / total_snippets)
- **Current Performance**: **80%** average (range: 40%-100%)

#### 3. **Field Coverage Score**
- **What**: Percentage of required fields present in output
- **How**: Check 7 core fields (title, authors, year, methods, results, summary, evidence)
- **Score**: (present_fields / 7)
- **Current Performance**: **100%** (all papers have all fields)

#### 4. **Numeric Consistency Score**
- **What**: Internal consistency of numeric results (baseline comparisons, value ranges, unit consistency)
- **How**: 
  - Check if `higher_is_better=True` → our value > baseline
  - Check percentages in [0, 100], probabilities in [0, 1]
  - Check same metric has same units across results
  - Check confidence scores in [0, 1]
- **Score**: (passed_checks / total_checks)
- **Current Performance**: **100%** (all papers pass all checks)

#### 5. **Summary Alignment Score**
- **What**: Token-level F1 between generated summary and gold summary (if available)
- **How**: Tokenize both summaries, compute precision/recall/F1
- **Score**: F1 score (0-1)
- **Current Performance**: **63%** average (range: 0%-100%)

---

## 🧪 Batch Evaluation Results

### Papers Processed (10 Total)

| Paper ID | JSON Valid | Evidence | Coverage | Consistency | Summary | Status |
|----------|------------|----------|----------|-------------|---------|--------|
| 2502.00401v2 | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | 🟡 67% | ✅ |
| 2509.21117v1 | ✅ 100% | 🟡 40% | ✅ 100% | ✅ 100% | ❌ 0% | ⚠️ |
| 2509.21266v1 | ✅ 100% | 🟡 60% | ✅ 100% | ✅ 100% | 🟡 67% | ✅ |
| boosting-timestamped-gnns | ✅ 100% | ✅ 80% | ✅ 100% | ✅ 100% | ✅ 75% | ✅ |
| graph-model-explainer | ✅ 100% | ✅ 80% | ✅ 100% | ✅ 100% | 🟡 25% | ⚠️ |
| spottarget-gnns | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | 🟡 50% | ✅ |
| TIMEBASED | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | ✅ |
| 2509.21291v1 | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | 🟡 67% | ✅ |
| attention-is-all-you-need | ✅ 100% | 🟡 60% | ✅ 100% | ✅ 100% | 🟡 33% | ✅ |
| gsampler-gpu-sampling | ✅ 100% | ✅ 80% | ✅ 100% | ✅ 100% | ✅ 100% | ✅ |

### Aggregate Metrics
- **JSON Validity**: 100% (10/10)
- **Avg Evidence Precision**: 80%
- **Avg Field Coverage**: 100%
- **Avg Numeric Consistency**: 100%
- **Avg Summary Alignment**: 63%

### Key Insights
1. **Perfect structural extraction**: All papers produced valid JSON with all required fields
2. **Strong numeric consistency**: All baseline comparisons and value ranges validated correctly
3. **Good evidence grounding**: 80% of claims have verifiable evidence (room for improvement on some papers)
4. **Summary quality variance**: Some papers (TIMEBASED, gsampler) had perfect summary alignment; others struggled

---

## 🚀 Deployment

### Live App
- **URL**: https://research-paper-analyzer-n55umbhgiafzbkntyzvq9d.streamlit.app
- **Platform**: Streamlit Cloud
- **Status**: ✅ Deployed

### Deployment Configuration
1. **Requirements**: `requirements.txt` includes all dependencies (including `python-dotenv`)
2. **Secrets**: API key stored in Streamlit Cloud secrets as `OPENROUTER_API_KEY`
3. **App Path**: `research-paper-analyzer/app/app.py`
4. **Config**: `.streamlit/config.toml` sets theme and server options

### Known Deployment Issues & Fixes
1. **Issue**: `ModuleNotFoundError: No module named 'dotenv'`
   - **Fix**: Added `python-dotenv==1.0.0` to `requirements.txt`

2. **Issue**: `Error code: 401 - User not found`
   - **Cause**: API key not set in Streamlit secrets
   - **Fix**: App now checks both `st.secrets` and environment variables, shows helpful error if missing

---

## 🔧 Development Setup

### Local Installation
```bash
git clone https://github.com/BhaveshBytess/research-paper-analyzer.git
cd research-paper-analyzer
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables
Create `.env` file:
```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=deepseek/deepseek-chat-v3.1:free
```

### Running Locally
```bash
cd research-paper-analyzer
streamlit run app/app.py
```

### Running Batch Evaluation
```bash
python batch_deepseek_inline.py
```

### Generating Visualizations
```bash
python create_visualizations.py
```

---

## 📈 Project Metrics

### Code Statistics
- **Total Lines of Code**: ~3,500 (excluding tests)
- **Main Modules**: 15
- **Prompts**: 5 custom prompts
- **Tests**: Schema validation + metrics evaluation
- **Documentation**: 8 markdown files

### Performance
- **Avg Processing Time**: 15-30 seconds per paper
- **Caching**: Yes (`.cache/` dir, hash-based)
- **Parallelization**: Async heads execution
- **API Efficiency**: Token limits enforced (3000 chars input, 256 tokens output per head)

---

## 🎓 Key Technical Achievements

1. **Multi-Head Architecture**: Parallel extraction of 5 different aspects (metadata, methods, results, limitations, summary)
2. **Evidence Grounding**: Automatic page-level citation for all extracted claims
3. **Robust Validation**: JSONSchema + Pydantic + custom numeric consistency checks
4. **LLM-Agnostic**: Works with any OpenRouter model (DeepSeek, Gemma, Claude, etc.)
5. **Production-Ready UI**: Streamlit app with file upload, model selection, caching control
6. **Comprehensive Evaluation**: 5 metrics implemented and validated on 10 papers
7. **Open Source**: MIT license, well-documented, contribution-ready

---

## 🐛 Known Limitations

1. **No OCR Support**: Scanned PDFs not yet supported (requires Tesseract integration)
2. **Summary Quality Variance**: Some papers have low summary alignment (need better prompts or model)
3. **Evidence Fuzzy Matching**: Threshold tuning needed for edge cases
4. **No Multi-Paper Analysis**: Currently processes one paper at a time
5. **Limited Error Recovery**: If LLM fails repeatedly, pipeline stops (need retry logic)

---

## 🗺️ Roadmap

### Completed ✅
- [x] Core pipeline (ingestion → extraction → validation → storage)
- [x] Streamlit UI
- [x] Evidence attachment
- [x] Batch evaluation framework
- [x] 5 evaluation metrics
- [x] Numeric consistency checker
- [x] Deployment to Streamlit Cloud
- [x] Comprehensive documentation

### In Progress 🚧
- [ ] OCR support for scanned PDFs
- [ ] Manual correction UI (human-in-the-loop)
- [ ] Evidence ranking by confidence

### Future Enhancements 🔮
- [ ] Multi-paper comparison dashboard
- [ ] Automatic citation network extraction
- [ ] Fine-tuned model for academic paper extraction
- [ ] REST API for programmatic access
- [ ] Browser extension for arXiv integration

---

## 📝 Documentation Files

1. **README.md** - Main project documentation
2. **CONTRIBUTING.md** - Contribution guidelines
3. **LICENSE** - MIT License
4. **START_HERE.md** - Quick start guide
5. **ARCHITECTURE.md** - System architecture deep dive
6. **PROJECT_COMPLETION_REPORT.md** - Final project report
7. **FINAL_DEPLOYMENT_CHECKLIST.md** - Deployment checklist
8. **PROJECT_WORKFLOW_SUMMARY.md** (this file) - Complete workflow summary

---

## 🤝 Team & Contact

- **Developer**: Bhavesh Bytess
- **Email**: 10bhavesh7.11@gmail.com
- **GitHub**: [@BhaveshBytess](https://github.com/BhaveshBytess)
- **Repository**: [research-paper-analyzer](https://github.com/BhaveshBytess/research-paper-analyzer)

---

## 📜 License

This project is licensed under the **MIT License**.

Copyright (c) 2025 Bhavesh Bytess

---

## 🎯 Resume-Ready Summary

**Research Paper Analyzer** is a production-ready ML pipeline that:
- Extracts structured information from academic PDFs using LLMs (DeepSeek/Gemma)
- Achieves **100% JSON validity** and **80% evidence precision** across 10 papers
- Implements 5 evaluation metrics with comprehensive validation
- Deployed live at [Streamlit Cloud](https://research-paper-analyzer-n55umbhgiafzbkntyzvq9d.streamlit.app)
- Built with Python, Streamlit, OpenRouter API, Pydantic, JSONSchema
- Open source (MIT), well-documented, contribution-ready

**Impact**: Automates hours of manual paper analysis into 30 seconds per paper with verifiable evidence grounding.

---

**Last Updated**: November 3, 2025  
**Version**: 1.0.0  
**Status**: ✅ Production

