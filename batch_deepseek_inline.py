#!/usr/bin/env python
"""
INLINE BATCH EVALUATION - Processes 2 papers with DeepSeek
This version runs everything inline to avoid subprocess issues
"""

import sys
import os
import json
import csv
from pathlib import Path
from datetime import datetime, timezone
import traceback

# Set environment
os.environ["OPENROUTER_API_KEY"] = "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"
os.environ["LLM_MODE"] = "openrouter::deepseek/deepseek-chat-v3.1:free"

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "research-paper-analyzer"))

print("\n" + "="*60)
print("BATCH EVALUATION - Research Paper Analyzer")
print("="*60)
print(f"LLM: DeepSeek (OpenRouter)")
print(f"Batch Size: 2 papers")
print("="*60 + "\n")

# Import modules
try:
    from ingestion.parser import parse_pdf_to_pages
    from orchestrator.heads import HeadRunner, OpenRouterLLM, LLMGenerationError
    from orchestrator.pipeline import Pipeline
    from orchestrator.repair import Repairer
    from evidence.locator import attach_evidence_for_paper
    from validation.schema_validator import validate_with_jsonschema
    from eval.eval_metrics import field_coverage, numeric_consistency_check
    print("✓ Modules imported successfully\n")
except Exception as e:
    print(f"✗ Import error: {e}")
    traceback.print_exc()
    sys.exit(1)

# Import NLTK for sentence tokenization
try:
    from nltk.tokenize import sent_tokenize
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Downloading NLTK punkt tokenizer...")
        nltk.download('punkt', quiet=True)
except ImportError:
    print("Warning: NLTK not available, using simple sentence splitting")
    def sent_tokenize(text):
        return [s.strip() + '.' for s in text.split('.') if s.strip()]

# Import fuzzy matching
try:
    from rapidfuzz import fuzz
except ImportError:
    from difflib import SequenceMatcher
    class fuzz:
        @staticmethod
        def partial_ratio(a, b):
            return SequenceMatcher(None, a, b).ratio() * 100

# Configuration
SAMPLES_DIR = project_root / "samples"
RESULTS_DIR = project_root / "batch_eval_results"
RESULTS_CSV = RESULTS_DIR / "results.csv"
RESULTS_JSONL = RESULTS_DIR / "results.jsonl"
BATCH_SIZE = 2
FUZZY_THRESHOLD = 72.0

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def compute_summary_alignment(summary, evidence):
    """Compute alignment score between summary and evidence."""
    if not summary or not evidence:
        return 0.0
    
    sentences = [s.strip() for s in sent_tokenize(summary) if s.strip()]
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

def compute_evidence_precision(paper):
    """Compute evidence coverage."""
    evidence = paper.get("evidence", {})
    if not evidence:
        return 0.0
    
    expected_keys = ["title", "methods", "results", "limitations", "summary"]
    covered = sum(1 for key in expected_keys if evidence.get(key))
    return covered / len(expected_keys)

def process_paper(pdf_path):
    """Process a single paper."""
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
        # Parse PDF
        print("  [1/5] Parsing PDF...")
        parsed = parse_pdf_to_pages(str(pdf_path), save_json=False, out_dir=str(RESULTS_DIR / "temp"))
        pages = parsed.get("pages", [])
        print(f"        Extracted {len(pages)} pages")
        
        if not pages:
            result["notes"] = "No pages extracted"
            result["errors"].append("PDF parsing failed")
            return result
        
        # Build contexts
        print("  [2/5] Building contexts...")
        metadata_ctx = pages[0].get("clean_text", "")[:800]
        half = max(1, len(pages) // 2)
        methods_ctx = "\n\n".join(p.get("clean_text", "")[:400] for p in pages[:half])[:1200]
        results_ctx = "\n\n".join(p.get("clean_text", "")[:400] for p in pages)[:1600]
        limitations_ctx = "\n\n".join(p.get("clean_text", "")[:400] for p in pages[-2:])[:800]
        summary_ctx = pages[0].get("clean_text", "")[:600] + "\n\n" + pages[-1].get("clean_text", "")[:600]
        
        contexts = {
            "metadata": metadata_ctx,
            "methods": methods_ctx,
            "results": results_ctx,
            "limitations": limitations_ctx,
            "summary": summary_ctx[:1200],
        }
        
        # Run pipeline with DeepSeek
        print("  [3/5] Running extraction with DeepSeek...")
        api_key = os.environ.get("OPENROUTER_API_KEY")
        model_id = "deepseek/deepseek-chat-v3.1:free"
        
        llm_client = OpenRouterLLM(api_key=api_key, model_id=model_id)
        runner = HeadRunner(llm_client=llm_client)
        pipeline = Pipeline(head_runner=runner, cache_dir=str(project_root / ".cache"))
        merged = pipeline.run(contexts)
        
        # Repair
        print("  [4/5] Repairing and validating...")
        repairer = Repairer()
        repaired, applied, remaining = repairer.repair_json(merged, max_attempts=1)
        repaired.setdefault("_meta", {})["repair_log"] = applied
        
        # Attach evidence
        print("  [5/5] Attaching evidence...")
        final_paper, evidence_report = attach_evidence_for_paper(repaired, pages, fuzzy_threshold=85.0)
        final_paper["_meta"]["evidence_report"] = evidence_report
        
        # Compute metrics
        print("\n  Computing metrics:")
        
        errors = validate_with_jsonschema(final_paper)
        result["json_validity"] = 1.0 if not errors else 0.0
        print(f"    ✓ JSON Validity: {result['json_validity']:.2f}")
        
        result["evidence_precision"] = compute_evidence_precision(final_paper)
        print(f"    ✓ Evidence Precision: {result['evidence_precision']:.2f}")
        
        result["field_coverage"] = field_coverage({}, final_paper)
        print(f"    ✓ Field Coverage: {result['field_coverage']:.2f}")
        
        consistency = numeric_consistency_check(final_paper)
        result["numeric_consistency"] = consistency.get("consistency_score")
        if result["numeric_consistency"] is not None:
            print(f"    ✓ Numeric Consistency: {result['numeric_consistency']:.2f}")
        else:
            print(f"    ✓ Numeric Consistency: N/A")
        
        result["summary_alignment"] = compute_summary_alignment(
            final_paper.get("summary", ""),
            final_paper.get("evidence", {})
        )
        print(f"    ✓ Summary Alignment: {result['summary_alignment']:.2f}")
        
        # Save paper JSON
        paper_json = RESULTS_DIR / f"{pdf_path.stem}.json"
        with open(paper_json, "w", encoding="utf-8") as f:
            json.dump(final_paper, f, ensure_ascii=False, indent=2)
        print(f"\n  ✓ Saved to: {paper_json.name}")
        
    except LLMGenerationError as e:
        result["notes"] = f"LLM error: {str(e)}"
        result["errors"].append(str(e))
        print(f"\n  ✗ LLM Error: {e}")
        if "quota" in str(e).lower() or "rate" in str(e).lower():
            raise
    except Exception as e:
        result["notes"] = f"Error: {str(e)}"
        result["errors"].append(str(e))
        print(f"\n  ✗ Error: {e}")
        traceback.print_exc()
    
    return result

def save_result(result):
    """Save result to CSV and JSONL."""
    csv_exists = RESULTS_CSV.exists()
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["paper_id", "filename", "timestamp", "json_validity", "evidence_precision",
                     "field_coverage", "numeric_consistency", "summary_alignment", "notes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not csv_exists:
            writer.writeheader()
        writer.writerow({k: result.get(k, "") for k in fieldnames})
    
    with open(RESULTS_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

# Main execution
if __name__ == "__main__":
    # Find PDFs
    pdf_files = sorted([f for f in SAMPLES_DIR.glob("**/*") if f.suffix.lower() == ".pdf"])
    
    if not pdf_files:
        print("ERROR: No PDF files found!")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDFs total")
    
    # Check for already processed papers
    already_processed = set()
    if RESULTS_CSV.exists():
        import csv as csv_mod
        with open(RESULTS_CSV, 'r', encoding='utf-8') as f:
            reader = csv_mod.DictReader(f)
            for row in reader:
                already_processed.add(row['filename'])
    
    # Filter out already processed
    unprocessed = [f for f in pdf_files if f.name not in already_processed]
    
    if already_processed:
        print(f"Already processed: {len(already_processed)} papers")
    print(f"Remaining to process: {len(unprocessed)} papers")
    
    if not unprocessed:
        print("\n✓ All papers already processed!")
        sys.exit(0)
    
    # Process next batch
    batch = unprocessed[:BATCH_SIZE]
    print(f"\nProcessing next {len(batch)} papers:")
    for i, pdf in enumerate(batch, 1):
        print(f"  {i}. {pdf.name}")
    print()
    
    # Process
    for idx, pdf_path in enumerate(batch, 1):
        try:
            result = process_paper(pdf_path)
            save_result(result)
            print(f"\nProgress: {idx}/{len(batch)} completed\n")
        except LLMGenerationError as e:
            if "quota" in str(e).lower():
                print("\n" + "!"*60)
                print("QUOTA LIMIT REACHED - STOPPING")
                print("!"*60)
                break
    
    print("\n" + "="*60)
    print("BATCH EVALUATION COMPLETE")
    print("="*60)
    print(f"Results: {RESULTS_CSV}")
    print(f"Papers: {RESULTS_DIR}")
    print("="*60)
