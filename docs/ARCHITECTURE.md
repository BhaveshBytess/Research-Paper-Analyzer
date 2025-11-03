# Research Paper Analyzer - Architecture Documentation

## System Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INPUT LAYER                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │  Streamlit   │    │     CLI      │    │  Python API  │         │
│  │     UI       │    │   Interface  │    │   Interface  │         │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘         │
│         └──────────────────┬─┴────────────────────┘                │
└────────────────────────────┼──────────────────────────────────────┘
                             ↓
┌────────────────────────────┼──────────────────────────────────────┐
│                  PDF PARSING LAYER                                 │
│              ┌─────────────────┐                                   │
│              │  PDF Parser     │                                   │
│              │  (PyMuPDF)      │                                   │
│              └────────┬────────┘                                   │
│                       ↓                                            │
│    ┌──────────────────┴──────────────────────┐                    │
│    │  Text  │  Layout  │  Metadata  │  Pages │                    │
│    └──────────────────┬──────────────────────┘                    │
└───────────────────────┼─────────────────────────────────────────┘
                        ↓
┌───────────────────────┼─────────────────────────────────────────┐
│              CONTEXT BUILDING LAYER                              │
│           ┌─────────────────┐                                    │
│           │  Context Builder│                                    │
│           └────────┬────────┘                                    │
│                    ↓                                             │
│    ┌───────────────┼───────────────┐                            │
│    │ • Metadata Context            │                            │
│    │ • Methods Context             │                            │
│    │ • Results Context             │                            │
│    │ • Limitations Context         │                            │
│    │ • Summary Context             │                            │
│    └───────────────┬───────────────┘                            │
└────────────────────┼────────────────────────────────────────────┘
                     ↓
┌────────────────────┼────────────────────────────────────────────┐
│            LLM EXTRACTION LAYER                                  │
│         ┌──────────────────┐                                     │
│         │  LLM Extractor   │                                     │
│         │  (Model-Agnostic)│                                     │
│         └────────┬─────────┘                                     │
│                  ↓                                                │
│    ┌─────────────┼─────────────┐                                │
│    │  DeepSeek | Gemma | Claude │                                │
│    │      OpenRouter API         │                                │
│    └─────────────┬─────────────┘                                │
│                  ↓                                                │
│         ┌─────────────────┐                                      │
│         │  Raw JSON       │                                      │
│         └────────┬────────┘                                      │
└──────────────────┼─────────────────────────────────────────────┘
                   ↓
┌──────────────────┼─────────────────────────────────────────────┐
│       REPAIR & VALIDATION LAYER                                  │
│    ┌──────────────────────┐                                     │
│    │  JSON Repair Engine  │                                     │
│    └──────────┬───────────┘                                     │
│               ↓                                                  │
│    ┌──────────┴───────────┐                                     │
│    │  Fix → Validate →    │                                     │
│    │  Schema Check        │                                     │
│    └──────────┬───────────┘                                     │
│               ↓                                                  │
│    ┌──────────────────┐                                         │
│    │ Validated Paper  │                                         │
│    └──────────┬───────┘                                         │
└───────────────┼────────────────────────────────────────────────┘
                ↓
┌───────────────┼────────────────────────────────────────────────┐
│     CONSISTENCY CHECK LAYER                                      │
│    ┌──────────────────┐                                         │
│    │  Numeric         │                                         │
│    │  Consistency     │                                         │
│    │  Validator       │                                         │
│    └──────────┬───────┘                                         │
│               ↓                                                  │
│    Checks: Ranges | Units | Logic | Confidence                  │
│               ↓                                                  │
│    ┌──────────────────┐                                         │
│    │ Consistency OK   │                                         │
│    └──────────┬───────┘                                         │
└───────────────┼────────────────────────────────────────────────┘
                ↓
┌───────────────┼────────────────────────────────────────────────┐
│     EVIDENCE ATTACHMENT LAYER                                    │
│    ┌──────────────────┐                                         │
│    │  Evidence        │                                         │
│    │  Matcher         │                                         │
│    │  (Fuzzy 85%)     │                                         │
│    └──────────┬───────┘                                         │
│               ↓                                                  │
│    Search → Match → Extract → Link Pages                        │
│               ↓                                                  │
│    ┌──────────────────┐                                         │
│    │ Evidence-Enriched│                                         │
│    │     Paper        │                                         │
│    └──────────┬───────┘                                         │
└───────────────┼────────────────────────────────────────────────┘
                ↓
┌───────────────┼────────────────────────────────────────────────┐
│          OUTPUT LAYER                                            │
│    ┌──────────────────┐                                         │
│    │  Structured JSON │                                         │
│    │  + Evidence      │                                         │
│    │  + Metadata      │                                         │
│    └──────────┬───────┘                                         │
│               ↓                                                  │
│    ┌──────────┴───────────┐                                     │
│    │  Save | Display | API│                                     │
│    └──────────────────────┘                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. PDF Parser (`pdf_parser.py`)
**Purpose:** Extract text and metadata from PDF files

**Key Functions:**
- `parse_pdf(path: str) -> List[str]`: Main entry point
- `extract_text_pymupdf()`: Primary extraction
- `extract_layout()`: Layout analysis

**Dependencies:** PyMuPDF, pdfplumber

### 2. Context Builder (`llm_extractor.py`)
**Purpose:** Prepare focused contexts for extraction

**Extraction Heads:**
1. Metadata (title, authors, venue)
2. Methods (architectures, algorithms)
3. Results (metrics, datasets)
4. Limitations
5. Summary

**Strategy:** Semantic chunking, 4000 token max, 200 token overlap

### 3. LLM Extractor (`llm_extractor.py`)
**Purpose:** Call LLM APIs with structured prompts

**Models:** DeepSeek v3.1, Gemma 2-9B, Claude 3.5

**Features:** Auto-retry (3x), JSON mode, caching

### 4. Schema Validator (`schema.py`)
**Purpose:** Enforce output structure

**Layers:**
1. JSON Schema (structure)
2. Pydantic Models (types)
3. Custom Validators (business logic)

### 5. Numeric Consistency Checker (`eval_metrics.py`)
**Purpose:** Detect hallucinated metrics

**Checks:**
- Value ranges (0-100 for %)
- Confidence (0-1)
- Baseline logic
- Unit consistency

**Output:** 1.0 (pass) or 0.0 (fail) + details

### 6. Evidence Matcher (`evidence_matcher.py`)
**Purpose:** Link claims to source text

**Algorithm:**
1. Extract key terms
2. Fuzzy search (85% threshold)
3. Extract snippet (±50 chars)
4. Attach page number

---

## Performance

### Latency
- Parsing: ~1-2s
- LLM: ~10-15s
- Validation: <1s
- Evidence: ~2-3s
- **Total: ~15-20s per paper**

### Throughput
- Single: 3 papers/min
- Batch: 2 papers/min (rate limited)

### Resources
- Memory: ~200MB per paper
- Disk: ~10KB per JSON
- API: 5 calls per paper

---

## Error Handling

### Types
1. PDF parse errors
2. LLM API errors
3. Validation errors
4. Evidence errors

### Recovery
- Retry (3x with backoff)
- Fallback models
- Partial results
- Checkpointing

---

**Last Updated:** 2025-11-03  
**Version:** 1.1.0
