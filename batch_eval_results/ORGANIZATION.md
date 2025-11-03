# Batch Evaluation Results - Organization

**Date:** 2025-11-02  
**Status:** Organized ✅

---

## Structure

### 1. Individual Paper Results

Each successfully processed paper has its results in:
```
samples/{paper_name}/evaluation/
  ├── extracted_paper.json    # Full extraction with evidence
  └── README.md               # Quick metrics summary
```

**Papers with evaluation:**
- ✅ 2502.00401v2 (SPECTRO-RIEMANNIAN GNNs)
- ✅ 2509.21117v1
- ✅ 2509.21266v1
- ✅ boosting-the-performance-of-deployable-timestamped-directed-gnns-via-time-relaxed-sampling
- ✅ graph-model-explainer-tool
- ✅ gsampler-general-and-efficient-gpu-based-graph-sampling-for-graph-learning

**Papers pending (failed due to rate limit or errors):**
- ⏳ 2509.21291v1 (LLM parse error)
- ⏳ 2509.21310v1 (LLM parse error)
- ⏳ spottarget (rate limit)
- ⏳ TIMEBASED (rate limit)

---

### 2. Aggregate Results

**Location:** `batch_eval_results/`

**Main files:**
- `results.csv` - Complete metrics table for all papers
- `results.jsonl` - Full JSON log with errors

**Summary reports:** `batch_eval_results/summary/`
- `COMPLETE_EVALUATION_REPORT.md` - Full analysis with metrics, errors, recommendations
- `REAL_PAPERS_SUMMARY.md` - Detailed per-paper breakdown
- `EVALUATION_SUMMARY.md` - Initial test run summary

---

## Quick Access

### View specific paper results:
```bash
# Example: View gsampler results (best paper - perfect scores!)
cat samples/gsampler-general-and-efficient-gpu-based-graph-sampling-for-graph-learning/evaluation/extracted_paper.json | python -m json.tool

# View its metrics
cat samples/gsampler-general-and-efficient-gpu-based-graph-sampling-for-graph-learning/evaluation/README.md
```

### View aggregate metrics:
```bash
# CSV format
cat batch_eval_results/results.csv

# Full report
cat batch_eval_results/summary/COMPLETE_EVALUATION_REPORT.md
```

---

## Metrics Summary (6 Successful Papers)

| Metric | Average Score | Status |
|--------|---------------|--------|
| JSON Validity | 1.00 | ✅ Perfect |
| Evidence Precision | 0.73 | 🟡 Good |
| Field Coverage | 1.00 | ✅ Perfect |
| **Numeric Consistency** | **1.00** | ✅ **Perfect!** |
| Summary Alignment | 0.56 | 🟡 Moderate |

---

## Best Performers

🥇 **gsampler** - Perfect 1.00 on ALL metrics  
🥈 **boosting-gnn** - 0.80 evidence, 0.75 alignment  
🥉 **2502.00401v2** - 1.00 evidence precision

---

## Next Steps

To process the remaining 4 papers (after rate limit reset):
```bash
python batch_deepseek_inline.py
```

This will automatically skip already processed papers and continue with the remaining ones.

---

**Organization completed:** 2025-11-02T21:08:30 UTC
