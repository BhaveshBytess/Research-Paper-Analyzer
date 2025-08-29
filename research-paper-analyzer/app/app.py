# app/app.py
import streamlit as st
import tempfile
import json
import os
from pathlib import Path
from datetime import datetime
from pprint import pprint

# Import pipeline pieces
from ingestion.parser import parse_pdf_to_pages
from orchestrator.heads import HeadRunner
from orchestrator.pipeline import Pipeline
from orchestrator.repair import Repairer
from evidence.locator import attach_evidence_for_paper
from store.store import save_paper, list_papers, load_paper

# Configuration
st.set_page_config(page_title="Research Paper Analyzer", layout="wide")
st.title("Research Paper Analyzer — Resume Demo")
st.markdown(
    """
    Upload a research paper (PDF). The app will:
    1. Parse the PDF into pages.
    2. Run task-specific heads (metadata, methods, results, limitations, summary) with a **Mock LLM** (offline).
    3. Merge results → run heuristic repairs → attach page-level evidence snippets.
    4. Show the validated JSON, summary, evidence, repair log, and let you save the JSON locally.
    
    *This demo runs offline (no paid API keys required).*
    """
)

# Helper: small utility to pretty print JSON in Streamlit and allow download
def pretty_json_download(data: dict, filename: str = "paper.json"):
    s = json.dumps(data, ensure_ascii=False, indent=2)
    st.download_button(label="Download JSON", data=s, file_name=filename, mime="application/json")

# Helper: show evidence nicely
def show_evidence(evidence: dict):
    if not evidence:
        st.info("No evidence attached.")
        return
    for key, items in evidence.items():
        st.subheader(f"Evidence — {key}")
        for i, it in enumerate(items):
            page = it.get("page")
            snippet = it.get("snippet")
            st.markdown(f"- **Page {page}** — {snippet}")

# Processing function (used both by UI and tests if needed)
def process_pdf(filepath: str, run_store_save: bool = False):
    """
    End-to-end local processing pipeline:
      - parse pdf -> pages
      - build naive contexts from pages (first page for metadata, whole doc for results)
      - run heads through Pipeline (MockLLM)
      - merge -> repair -> attach evidence
    Returns (final_paper_dict, debug_info)
    """
    debug = {"steps": [], "timings": {}}
    t0 = datetime.utcnow()

    # 1) Parse
    debug["steps"].append("parsing")
    parsed = parse_pdf_to_pages(filepath, save_json=False, out_dir="outputs")
    pages = parsed.get("pages", [])
    debug["timings"]["parsing"] = (datetime.utcnow() - t0).total_seconds()

    # Build simple contexts (Stage 2 will make this smarter)
    # metadata: first page
    metadata_ctx = pages[0]["clean_text"] if pages else ""
    # methods: first half of pages
    half = max(1, len(pages)//2)
    methods_ctx = "\n\n".join([p.get("clean_text","") for p in pages[:half]])
    # results: entire doc
    results_ctx = "\n\n".join([p.get("clean_text","") for p in pages])
    # limitations: last 2 pages
    limitations_ctx = "\n\n".join([p.get("clean_text","") for p in pages[-2:]]) if pages else ""
    # summary: first page + last page
    summary_ctx = (pages[0].get("clean_text","") if pages else "") + "\n\n" + (pages[-1].get("clean_text","") if pages else "")

    contexts = {
        "metadata": metadata_ctx,
        "methods": methods_ctx,
        "results": results_ctx,
        "limitations": limitations_ctx,
        "summary": summary_ctx
    }

    # 2) Run heads (Pipeline)
    debug["steps"].append("running_heads")
    runner = HeadRunner()  # defaults to MockLLM in Stage 3
    pipeline = Pipeline(head_runner=runner, cache_dir=".cache")
    merged = pipeline.run(contexts)
    debug["timings"]["run_heads"] = (datetime.utcnow() - t0).total_seconds() - debug["timings"]["parsing"]

    # 3) Repair
    debug["steps"].append("repair")
    repairer = Repairer(llm_client=None)
    repaired, applied, remaining = repairer.repair_json(merged, max_attempts=1)
    debug["timings"]["repair"] = (datetime.utcnow() - t0).total_seconds() - debug["timings"]["parsing"] - debug["timings"]["run_heads"]
    repaired.setdefault("_meta", {})
    repaired["_meta"].setdefault("repair_log", [])
    repaired["_meta"]["repair_log"].extend(applied)
    repaired["_meta"]["remaining_errors"] = remaining

    # 4) Attach evidence
    debug["steps"].append("evidence_attach")
    final_paper, evidence_report = attach_evidence_for_paper(repaired, pages, fuzzy_threshold=85.0)
    final_paper.setdefault("_meta", {})
    final_paper["_meta"]["evidence_report"] = evidence_report
    debug["timings"]["total_elapsed"] = (datetime.utcnow() - t0).total_seconds()

    # optionally save into datastore
    if run_store_save:
        try:
            pid = save_paper(final_paper)
            final_paper["_meta"]["saved_paper_id"] = pid
        except Exception as e:
            final_paper["_meta"]["save_error"] = str(e)

    return final_paper, debug

# Sidebar: saved papers viewer & search
st.sidebar.header("Saved papers")
if st.sidebar.button("Refresh saved list"):
    st.experimental_rerun()

saved = list_papers()
if saved:
    opts = list(saved.items())
    # Show small list (title and year)
    rows = [f"{k} — {v.get('title')[:80]} ({v.get('year')})" for k, v in opts]
    sel = st.sidebar.selectbox("View saved paper (select)", ["-- none --"] + rows)
    if sel != "-- none --":
        idx = rows.index(sel)
        pid = opts[idx][0]
        item = load_paper(pid)
        st.sidebar.markdown(f"**{item.get('title')}**")
        if st.sidebar.button("Load into main view"):
            # put the loaded JSON into main display area
            st.session_state["loaded_paper"] = item

# Main upload panel
st.header("Upload PDF")
uploaded = st.file_uploader("Upload a research paper (PDF)", type=["pdf"], accept_multiple_files=False)

# If previously loaded paper exists in session, show option to display
if "loaded_paper" in st.session_state:
    st.info("A saved paper was loaded from the datastore. Use Process to re-run pipeline on its JSON or Save to store again.")
    loaded_p = st.session_state["loaded_paper"]
    if st.button("Show loaded paper JSON"):
        st.json(loaded_p)
    if st.button("Clear loaded paper"):
        st.session_state.pop("loaded_paper", None)
    st.markdown("---")

if uploaded:
    # save uploaded file to temp file
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tfile.write(uploaded.read())
    tfile.flush()
    st.success("File uploaded. Processing...")
    # Controls
    col1, col2 = st.columns([1, 1])
    with col1:
        run_and_save = st.checkbox("Also save to local datastore after processing", value=False)
    with col2:
        show_raw_parsed = st.checkbox("Show parsed pages (debug)", value=False)

    # Process
    with st.spinner("Running pipeline (local MockLLM). This may take a few seconds..."):
        try:
            final_paper, debug = process_pdf(tfile.name, run_store_save=run_and_save)
        except Exception as e:
            st.error(f"Processing failed: {e}")
            st.stop()

    # Display summary and key info
    st.subheader("Summary")
    st.write(final_paper.get("summary", "— (no summary)"))

    st.subheader("Validation & Repair")
    meta = final_paper.get("_meta", {})
    repair_log = meta.get("repair_log", [])
    remaining_errors = meta.get("remaining_errors", [])
    if repair_log:
        st.markdown("**Repair log (automatic repairs applied):**")
        for r in repair_log:
            st.markdown(f"- {r}")
    else:
        st.markdown("No automatic repairs applied.")

    if remaining_errors:
        st.warning("Remaining schema validation errors (manual review advised):")
        for e in remaining_errors:
            st.markdown(f"- {e}")
    else:
        st.success("No remaining validation errors (passes schema)")

    st.subheader("Evidence snippets")
    ev = final_paper.get("evidence", {})
    show_evidence(ev)

    st.subheader("Key results (extracted)")
    res = final_paper.get("results", [])
    if res:
        # simple table
        rows = []
        for r in res:
            rows.append({
                "dataset": r.get("dataset"),
                "metric": r.get("metric"),
                "value": r.get("value"),
                "unit": r.get("unit"),
                "split": r.get("split"),
                "baseline": r.get("baseline"),
                "ours": r.get("ours_is")
            })
        st.table(rows)
    else:
        st.write("No results extracted.")

    st.subheader("Full JSON")
    st.json(final_paper)
    pretty_json_download(final_paper, filename=f"{(final_paper.get('title') or 'paper').replace(' ','_')}.json")

    if run_and_save:
        st.success("Paper saved to local datastore (if validation passed). See sidebar to load saved papers.")
    st.markdown("---")
    st.write("Debug info")
    st.text(json.dumps(debug, indent=2))

else:
    st.info("Upload a PDF to process.")

st.markdown("---")
st.caption("Streamlit demo — use MockLLM for offline development. To switch to a real LLM, create a real HeadRunner with the provider client and pass it to Pipeline(head_runner=YourHeadRunner).")
