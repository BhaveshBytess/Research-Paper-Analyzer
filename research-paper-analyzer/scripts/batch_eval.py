#!/usr/bin/env python
"""Batch evaluation pipeline for a folder of research PDFs."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd

from nltk.tokenize import sent_tokenize
from rapidfuzz import fuzz

# Ensure repository modules are importable
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ingestion.parser import parse_pdf_to_pages
from orchestrator.heads import HeadRunner, OpenRouterLLM, LLMGenerationError
from orchestrator.pipeline import Pipeline
from orchestrator.repair import Repairer
from evidence.locator import attach_evidence_for_paper
from orchestrator.merge import merge_heads_to_paper
from schema.models import Paper

ALIGNMENT_THRESHOLD = 72
FUZZY_THRESHOLD = 65


@dataclass
class PaperMetrics:
    paper_id: str
    schema_pass: bool
    repair_count: int
    evidence_coverage: float
    alignment_pre: float
    alignment_post: float
    notes: Optional[str] = None


def discover_pdfs(folder: Path) -> List[Path]:
    pdfs = sorted(p for p in folder.glob("*.pdf"))
    return pdfs


def slugify(path: Path) -> str:
    return path.stem.replace(" ", "_")


def compute_alignment(summary: str, evidence: Dict[str, Any]) -> Tuple[float, int, int]:
    sent_list = [s.strip() for s in sent_tokenize(summary or "") if s.strip()]
    if not sent_list:
        return 0.0, 0, 0

    snippets: List[str] = []
    for bucket in evidence.values():
        for item in bucket:
            snippet = item.get("snippet")
            if snippet:
                snippets.append(snippet)

    if not snippets:
        return 0.0, 0, len(sent_list)

    matched = 0
    for sent_text in sent_list:
        fuzzy_best = max(fuzz.partial_ratio(sent_text.lower(), snippet.lower()) for snippet in snippets)
        if fuzzy_best >= ALIGNMENT_THRESHOLD:
            matched += 1

    score = matched / len(sent_list)
    return score, matched, len(sent_list)


def evidence_coverage_metric(evidence: Dict[str, Any]) -> float:
    if not evidence:
        return 0.0
    buckets = list(evidence.values())
    if not buckets:
        return 0.0
    covered = sum(1 for bucket in buckets if bucket)
    return covered / len(buckets)


def process_pdf(
    pdf_path: Path,
    output_dir: Path,
    retries: int = 2,
    backoff: float = 5.0,
) -> PaperMetrics:
    slug = slugify(pdf_path)
    work_dir = output_dir / slug
    work_dir.mkdir(parents=True, exist_ok=True)

    parsed = parse_pdf_to_pages(str(pdf_path), save_json=False, out_dir=str(work_dir))
    pages = parsed.get("pages", [])

    metadata_ctx = pages[0]["clean_text"] if pages else ""
    half = max(1, len(pages) // 2)
    methods_ctx = "\n\n".join(p.get("clean_text", "") for p in pages[:half])
    results_ctx = "\n\n".join(p.get("clean_text", "") for p in pages)
    limitations_ctx = "\n\n".join(p.get("clean_text", "") for p in pages[-2:]) if pages else ""
    summary_ctx = (pages[0].get("clean_text", "") if pages else "") + "\n\n" + (pages[-1].get("clean_text", "") if pages else "")

    contexts = {
        "metadata": metadata_ctx,
        "methods": methods_ctx,
        "results": results_ctx,
        "limitations": limitations_ctx,
        "summary": summary_ctx,
    }

    attempt = 0
    while True:
        try:
            llm = OpenRouterLLM()
            runner = HeadRunner(llm_client=llm)
            pipeline = Pipeline(head_runner=runner, cache_dir=str(work_dir / ".cache"))
            merged = pipeline.run(contexts)
            pre_repair = merged
            repairer = Repairer(llm_client=None)
            repaired, applied, remaining = repairer.repair_json(pre_repair, max_attempts=1)
            repaired.setdefault("_meta", {})
            repaired["_meta"].setdefault("repair_log", [])
            repaired["_meta"]["repair_log"].extend(applied)
            repaired["_meta"]["remaining_errors"] = remaining
            final_paper, evidence_report = attach_evidence_for_paper(repaired, pages, fuzzy_threshold=85.0)
            final_paper.setdefault("_meta", {})
            final_paper["_meta"]["evidence_report"] = evidence_report
            break
        except LLMGenerationError as err:
            attempt += 1
            if attempt > retries:
                raise RuntimeError(f"LLM error after {retries} retries: {err}") from err
            time.sleep(backoff * attempt)

    (work_dir / "pre_repair.json").write_text(json.dumps(pre_repair, ensure_ascii=False, indent=2))
    (work_dir / "final.json").write_text(json.dumps(final_paper, ensure_ascii=False, indent=2))
    (work_dir / "summary.txt").write_text(final_paper.get("summary", ""))

    schema_ok = True
    try:
        Paper(**final_paper)
    except Exception:
        schema_ok = False

    repair_count = len(final_paper.get("_meta", {}).get("repair_log", []))
    coverage = evidence_coverage_metric(final_paper.get("evidence", {}))

    alignment_pre, _, _ = compute_alignment(pre_repair.get("summary", ""), pre_repair.get("evidence", {}))
    alignment_post, _, _ = compute_alignment(final_paper.get("summary", ""), final_paper.get("evidence", {}))

    return PaperMetrics(
        paper_id=slug,
        schema_pass=schema_ok,
        repair_count=repair_count,
        evidence_coverage=coverage,
        alignment_pre=alignment_pre,
        alignment_post=alignment_post,
        notes=None,
    )


def aggregate_metrics(metrics: Iterable[PaperMetrics]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    rows = [m.__dict__ for m in metrics]
    df = pd.DataFrame(rows)
    summary = {
        "Papers": len(df),
        "Schema pass": f"{df['schema_pass'].sum()}/{len(df)}",
        "Avg fixes": df["repair_count"].mean() if not df.empty else 0.0,
        "Evidence found": f"{(df['evidence_coverage'] > 0).sum()}/{len(df)}" if not df.empty else "0/0",
        "Summary align pre→post": (
            f"{df['alignment_pre'].mean():.2f} → {df['alignment_post'].mean():.2f}"
            if not df.empty else "0.00 → 0.00"
        ),
    }
    return df, summary


def render_visuals(df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if df.empty:
        return

    plt.figure(figsize=(4, 3))
    pre = df["alignment_pre"].mean()
    post = df["alignment_post"].mean()
    plt.bar(["Pre"], [pre], color="#8888ff")
    plt.bar(["Post"], [post], color="#4caf50")
    plt.title("Average Summary Alignment")
    plt.ylabel("Score")
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(output_dir / "alignment_pre_post.png", dpi=150)
    plt.close()

    plt.figure(figsize=(4, 3))
    passes = df["schema_pass"].sum()
    fails = len(df) - passes
    plt.bar(["Pass"], [passes], color="#4caf50")
    plt.bar(["Fail"], [fails], bottom=[passes], color="#ff7043")
    plt.title("Schema Validation Results")
    plt.ylabel("# Papers")
    plt.tight_layout()
    plt.savefig(output_dir / "schema_pass.png", dpi=150)
    plt.close()


def main(args: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Batch evaluation for research PDFs")
    parser.add_argument("pdf_dir", type=str, help="Folder containing PDF files")
    parser.add_argument("--output", type=str, default="results/batch_eval", help="Output directory")
    parser.add_argument("--retries", type=int, default=2, help="Retries for OpenRouter calls")
    parser.add_argument("--backoff", type=float, default=5.0, help="Backoff seconds between retries")
    opts = parser.parse_args(args)

    pdf_dir = Path(opts.pdf_dir)
    if not pdf_dir.exists():
        raise FileNotFoundError(pdf_dir)

    pdfs = discover_pdfs(pdf_dir)
    if not pdfs:
        print("No PDF files found.")
        return

    output_root = Path(opts.output)
    output_root.mkdir(parents=True, exist_ok=True)
    metrics: List[PaperMetrics] = []

    for pdf_path in pdfs:
        slug = slugify(pdf_path)
        try:
            metrics.append(
                process_pdf(
                    pdf_path,
                    output_dir=output_root,
                    retries=opts.retries,
                    backoff=opts.backoff,
                )
            )
        except Exception as exc:
            metrics.append(
                PaperMetrics(
                    paper_id=slug,
                    schema_pass=False,
                    repair_count=0,
                    evidence_coverage=0.0,
                    alignment_pre=0.0,
                    alignment_post=0.0,
                    notes=str(exc),
                )
            )
            continue

    df, summary = aggregate_metrics(metrics)
    df.to_csv(output_root / "metrics.csv", index=False)

    render_visuals(df, output_root)

    (output_root / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
