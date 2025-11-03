# Development Scripts

This folder contains utility scripts used during development and testing. These are **not part of the main application pipeline** but are useful for batch processing, evaluation, and visualization.

## Scripts

### `batch_deepseek_inline.py`
Batch processing script for running paper extraction on multiple PDFs sequentially.

**Usage:**
```bash
python scripts/dev/batch_deepseek_inline.py
```

### `create_visualizations.py`
Generates evaluation metric visualizations from batch results.

**Usage:**
```bash
python scripts/dev/create_visualizations.py
```

### `run_now.py`
Quick-run script for single paper extraction (development testing).

**Usage:**
```bash
python scripts/dev/run_now.py
```

## Note
For production use, please use the main Streamlit application:
```bash
streamlit run research-paper-analyzer/app/app.py
```
