#!/usr/bin/env python
"""
Batch Evaluation Runner for Research Paper Analyzer
Processes 2 papers per batch with quota monitoring
"""

import sys
import os
import json
import csv
from pathlib import Path
from datetime import datetime, timezone
import traceback

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "research-paper-analyzer"))

from ingestion.parser import parse_pdf_to_pages
from orchestrator.heads import HeadRunner, OpenRouterLLM, LLMGenerationError
from orchestrator.pipeline import Pipeline
from orchestrator.repair import Repairer
from evidence.locator import attach_evidence_for_paper
from validation.schema_validator import validate_with_jsonschema
from eval.eval_metrics import field_coverage, numeric_consistency_check
from nltk.tokenize import sent_tokenize
try:
    from rapidfuzz import fuzz
except ImportError:
    from difflib import SequenceMatcher
    def fuzz_ratio(a, b):
        return SequenceMatcher(None, a, b).ratio() * 100
    class fuzz:
        @staticmethod
        def partial_ratio(a, b):
            return fuzz_ratio(a, b)

# Configuration
SAMPLES_DIR = Path("samples")
RESULTS_DIR = Path("batch_eval_results")
CHECKPOINT_FILE = RESULTS_DIR / "checkpoint.json"
RESULTS_CSV = RESULTS_DIR / "results.csv"
RESULTS_JSONL = RESULTS_DIR / "results.jsonl"
BATCH_SIZE = 2
FUZZY_THRESHOLD = 72.0

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def compute_summary_alignment(summary: str, evidence: dict) -> float:
    """Compute alignment score between summary sentences and evidence snippets."""
    if not summary or not evidence:
        return 0.0
    
    try:
        sentences = [s.strip() for s in sent_tokenize(summary) if s.strip()]
    except:
        sentences = [s.strip() for s in summary.split('.') if s.strip()]
    
    if not sentences:
        return 0.0
    
    snippets = []
    for bucket in evidence.values():
        if isinstance(bucket, list):
            for item in bucket:
                snippet = item.get("snippet")
                if snippet:
                    snippets.append(snippet)
    
    if not snippets:
        return 0.0
    
    matched = 0
    for sent in sentences:
        best_score = max(fuzz.partial_ratio(sent.lower(), snip.lower()) for snip in snippets)
        if best_score >= FUZZY_THRESHOLD:
            matched += 1
    
    return matched / len(sentences)

def compute_evidence_precision(paper: dict) -> float:
    """Compute evidence coverage - fraction of expected keys with evidence."""
    evidence = paper.get("evidence", {})
    if not evidence:
        return 0.0
    
    expected_keys = ["title", "methods", "results", "limitations", "summary"]
    covered = 0
    
    for key in expected_keys:
        items = evidence.get(key, [])
        if items and len(items) > 0:
            covered += 1
    
    return covered / len(expected_keys)

def process_single_paper(pdf_path: Path, llm_choice: str = "offline") -> dict:
    """Process a single PDF and compute all metrics."""
    print(f"\n{'='*60}")
    print(f"Processing: {pdf_path.name}")
    print(f"{'='*60}")
    
    result = {
        "paper_id": pdf_path.stem,
        "filename": pdf_path.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "json_validity": None,
        "evidence_precision": None,
        "field_coverage": None,
        "numeric_consistency": None,
        "summary_alignment": None,
        "notes": "",
        "errors": []
    }
    
    try:
        # Step 1: Parse PDF
        print("  [1/5] Parsing PDF...")
        parsed = parse_pdf_to_pages(str(pdf_path), save_json=False, out_dir="outputs")
        pages = parsed.get("pages", [])
        
        if not pages:
            result["notes"] = "No pages extracted from PDF"
            result["errors"].append("PDF parsing failed - no pages")
            return result
        
        print(f"        Extracted {len(pages)} pages")
        
        # Step 2: Build contexts
        print("  [2/5] Building contexts...")
        metadata_ctx = pages[0].get("clean_text", "")[:800] if pages else ""
        half = max(1, len(pages) // 2)
        methods_ctx = "\n\n".join(p.get("clean_text", "")[:400] for p in pages[:half])[:1200]
        results_ctx = "\n\n".join(p.get("clean_text", "")[:400] for p in pages)[:1600]
        limitations_ctx = "\n\n".join(p.get("clean_text", "")[:400] for p in pages[-2:])[:800] if pages else ""
        summary_ctx = (pages[0].get("clean_text", "")[:600] if pages else "") + "\n\n" + (pages[-1].get("clean_text", "")[:600] if pages else "")
        summary_ctx = summary_ctx[:1200]
        
        contexts = {
            "metadata": metadata_ctx,
            "methods": methods_ctx,
            "results": results_ctx,
            "limitations": limitations_ctx,
            "summary": summary_ctx,
        }
        
        # Step 3: Run pipeline
        print(f"  [3/5] Running extraction pipeline (mode: {llm_choice})...")
        
        if llm_choice.startswith("openrouter::"):
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if not api_key:
                result["notes"] = "OPENROUTER_API_KEY not set"
                result["errors"].append("Missing API key")
                return result
            model_id = llm_choice.split("::", 1)[1]
            llm_client = OpenRouterLLM(api_key=api_key, model_id=model_id)
            runner = HeadRunner(llm_client=llm_client)
        else:
            runner = HeadRunner()  # MockLLM
        
        pipeline = Pipeline(head_runner=runner, cache_dir=".cache")
        merged = pipeline.run(contexts)
        
        # Step 4: Repair
        print("  [4/5] Repairing and validating...")
        repairer = Repairer(llm_client=None)
        repaired, applied, remaining = repairer.repair_json(merged, max_attempts=1)
        repaired.setdefault("_meta", {})
        repaired["_meta"]["repair_log"] = applied
        repaired["_meta"]["remaining_errors"] = remaining
        
        # Step 5: Attach evidence
        print("  [5/5] Attaching evidence...")
        final_paper, evidence_report = attach_evidence_for_paper(repaired, pages, fuzzy_threshold=85.0)
        final_paper["_meta"]["evidence_report"] = evidence_report
        
        # Compute metrics
        print("\n  Computing metrics:")
        
        # Metric 1: JSON Validity
        errors = validate_with_jsonschema(final_paper)
        result["json_validity"] = 1.0 if len(errors) == 0 else 0.0
        print(f"    ✓ JSON Validity: {result['json_validity']:.2f}")
        if errors:
            result["notes"] += f"Schema errors: {len(errors)}. "
        
        # Metric 2: Evidence Precision
        result["evidence_precision"] = compute_evidence_precision(final_paper)
        print(f"    ✓ Evidence Precision: {result['evidence_precision']:.2f}")
        
        # Metric 3: Field Coverage
        result["field_coverage"] = field_coverage({}, final_paper)
        print(f"    ✓ Field Coverage: {result['field_coverage']:.2f}")
        
        # Metric 4: Numeric Consistency
        consistency = numeric_consistency_check(final_paper)
        result["numeric_consistency"] = consistency.get("consistency_score")
        if result["numeric_consistency"] is not None:
            print(f"    ✓ Numeric Consistency: {result['numeric_consistency']:.2f}")
            if consistency.get("failed_checks"):
                result["notes"] += f"Consistency issues: {len(consistency['failed_checks'])}. "
        else:
            print(f"    ✓ Numeric Consistency: N/A (no results)")
        
        # Metric 5: Summary Alignment
        result["summary_alignment"] = compute_summary_alignment(
            final_paper.get("summary", ""),
            final_paper.get("evidence", {})
        )
        print(f"    ✓ Summary Alignment: {result['summary_alignment']:.2f}")
        
        # Save paper JSON
        paper_json_path = RESULTS_DIR / f"{pdf_path.stem}.json"
        with open(paper_json_path, "w", encoding="utf-8") as f:
            json.dump(final_paper, f, ensure_ascii=False, indent=2)
        
        print(f"\n  ✓ Paper processed successfully")
        print(f"  ✓ Saved to: {paper_json_path.name}")
        
    except LLMGenerationError as e:
        result["notes"] = f"LLM error: {str(e)}"
        result["errors"].append(str(e))
        print(f"\n  ✗ LLM Generation Error: {e}")
        
        # Check for quota errors
        if "quota" in str(e).lower() or "rate limit" in str(e).lower():
            raise  # Re-raise to trigger checkpoint
        
    except Exception as e:
        result["notes"] = f"Error: {str(e)}"
        result["errors"].append(str(e))
        print(f"\n  ✗ Error: {e}")
        traceback.print_exc()
    
    return result

def load_checkpoint():
    """Load checkpoint if exists."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return None

def save_checkpoint(last_completed, remaining, status):
    """Save checkpoint."""
    checkpoint = {
        "last_completed_paper": last_completed,
        "remaining_papers": remaining,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2)
    print(f"\n{'='*60}")
    print(f"CHECKPOINT SAVED: {CHECKPOINT_FILE}")
    print(f"Status: {status}")
    print(f"Last completed: {last_completed}")
    print(f"Remaining: {len(remaining)} papers")
    print(f"{'='*60}")

def append_result_to_logs(result):
    """Append result to CSV and JSONL logs."""
    # CSV
    csv_exists = RESULTS_CSV.exists()
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["paper_id", "filename", "timestamp", "json_validity", "evidence_precision", 
                     "field_coverage", "numeric_consistency", "summary_alignment", "notes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not csv_exists:
            writer.writeheader()
        writer.writerow({k: result.get(k, "") for k in fieldnames})
    
    # JSONL
    with open(RESULTS_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

def main():
    print("\n" + "="*60)
    print("BATCH EVALUATION - Research Paper Analyzer")
    print("="*60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Batch size: {BATCH_SIZE} papers")
    print(f"Samples directory: {SAMPLES_DIR}")
    print(f"Results directory: {RESULTS_DIR}")
    print("="*60 + "\n")
    
    # Discover PDFs
    pdf_files = sorted([f for f in SAMPLES_DIR.glob("**/*") if f.suffix.lower() == ".pdf"])
    
    if not pdf_files:
        print("ERROR: No PDF files found in samples directory!")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    
    # Check for checkpoint
    checkpoint = load_checkpoint()
    if checkpoint:
        print(f"\nCheckpoint found: {checkpoint.get('status')}")
        print(f"Resuming from: {checkpoint.get('last_completed_paper')}")
        remaining_names = checkpoint.get("remaining_papers", [])
        pdf_files = [f for f in pdf_files if f.name in remaining_names]
    
    # Limit to batch size
    batch = pdf_files[:BATCH_SIZE]
    remaining = [f.name for f in pdf_files[BATCH_SIZE:]]
    
    print(f"\nProcessing {len(batch)} papers in this batch:")
    for i, pdf in enumerate(batch, 1):
        print(f"  {i}. {pdf.name}")
    
    if remaining:
        print(f"\n{len(remaining)} papers will remain for next batch")
    
    # Get LLM choice from environment or use DeepSeek by default
    llm_mode = os.environ.get("LLM_MODE", "openrouter::deepseek/deepseek-chat-v3.1:free")
    print(f"\nLLM Mode: {llm_mode}")
    
    # Check for API key if using OpenRouter
    if llm_mode.startswith("openrouter::"):
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("\nERROR: OPENROUTER_API_KEY environment variable not set!")
            print("Please set it before running with OpenRouter models.")
            print("Example: set OPENROUTER_API_KEY=your_key_here")
            return
    
    # Process batch
    completed = []
    
    for idx, pdf_path in enumerate(batch, 1):
        try:
            result = process_single_paper(pdf_path, llm_choice=llm_mode)
            append_result_to_logs(result)
            completed.append(pdf_path.name)
            
            print(f"\nProgress: {idx}/{len(batch)} papers completed")
            
        except LLMGenerationError as e:
            # Quota/rate limit hit
            if "quota" in str(e).lower() or "rate limit" in str(e).lower() or "429" in str(e):
                print(f"\n{'!'*60}")
                print("QUOTA/RATE LIMIT REACHED")
                print(f"{'!'*60}")
                save_checkpoint(
                    last_completed=completed[-1] if completed else None,
                    remaining=[batch[idx].name] + remaining,  # Include current + rest
                    status="Quota reached - resume later"
                )
                return
            raise
    
    # All completed successfully
    print(f"\n{'='*60}")
    print("BATCH COMPLETED SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"Processed: {len(completed)} papers")
    print(f"Results saved to: {RESULTS_CSV}")
    
    if remaining:
        save_checkpoint(
            last_completed=completed[-1] if completed else None,
            remaining=remaining,
            status="Batch complete - more papers remaining"
        )
    else:
        print("\n✓ ALL PAPERS PROCESSED!")
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
            print("✓ Checkpoint cleared")
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
