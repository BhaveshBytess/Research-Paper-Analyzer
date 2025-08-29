# ingestion/parser.py
import fitz  # PyMuPDF
import pdfplumber
import json
import os
import argparse
import re
from typing import List, Dict, Any, Optional


def clean_text_whitespace(s: str) -> str:
    # Normalize whitespace, remove repeated newlines, trim
    s = re.sub(r"\r\n", "\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def blocks_from_pymupdf_page(page) -> List[Dict[str, Any]]:
    # page.get_text("blocks") -> list of (x0, y0, x1, y1, "text", block_no)
    raw_blocks = page.get_text("blocks")
    # sort by y (top) then x (left)
    raw_blocks.sort(key=lambda b: (b[1], b[0]))
    blocks = []
    for b in raw_blocks:
        x0, y0, x1, y1, text, *rest = b
        text = text.strip()
        if not text:
            continue
        blocks.append({
            "bbox": [float(x0), float(y0), float(x1), float(y1)],
            "text": clean_text_whitespace(text)
        })
    return blocks


def parse_with_pymupdf(path: str) -> Optional[Dict[str, Any]]:
    try:
        doc = fitz.open(path)
    except Exception:
        return None

    pages = []
    total_text_len = 0
    for i in range(len(doc)):
        page = doc[i]
        try:
            raw_text = page.get_text("text") or ""
        except Exception:
            raw_text = ""
        blocks = blocks_from_pymupdf_page(page)
        clean_blocks_text = "\n\n".join([b["text"] for b in blocks]) if blocks else clean_text_whitespace(raw_text)
        clean_text = clean_text_whitespace(clean_blocks_text or raw_text)
        pages.append({
            "page_no": i + 1,
            "raw_text": raw_text,
            "blocks": blocks,
            "clean_text": clean_text
        })
        total_text_len += len(clean_text or "")
    return {"pages": pages, "total_text_len": total_text_len}


def parse_with_pdfplumber(path: str) -> Optional[Dict[str, Any]]:
    try:
        with pdfplumber.open(path) as pdf:
            pages = []
            total_text_len = 0
            for i, page in enumerate(pdf.pages):
                raw_text = page.extract_text() or ""
                # simple block heuristic: split lines and treat each line as block
                lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
                blocks = [{"bbox": None, "text": clean_text_whitespace(l)} for l in lines]
                clean_text = clean_text_whitespace("\n\n".join(lines))
                pages.append({
                    "page_no": i + 1,
                    "raw_text": raw_text,
                    "blocks": blocks,
                    "clean_text": clean_text
                })
                total_text_len += len(clean_text or "")
        return {"pages": pages, "total_text_len": total_text_len}
    except Exception:
        return None


def is_scanned(parsed: Dict[str, Any], threshold_chars: int = 200) -> bool:
    # If total extracted characters is below threshold, likely scanned PDF
    if parsed is None:
        return True
    total = parsed.get("total_text_len", 0)
    return total < threshold_chars


def parse_pdf_to_pages(path: str, save_json: bool = True, out_dir: str = "outputs") -> Dict[str, Any]:
    path = os.path.abspath(path)
    basename = os.path.splitext(os.path.basename(path))[0]
    # Try PyMuPDF first
    parsed = parse_with_pymupdf(path)
    parser_used = "pymupdf"
    if parsed is None or parsed.get("total_text_len", 0) == 0:
        # fallback
        parsed = parse_with_pdfplumber(path)
        parser_used = "pdfplumber" if parsed is not None else "none"

    scanned = is_scanned(parsed)

    result = {
        "file": path,
        "basename": basename,
        "parser_used": parser_used,
        "needs_ocr": scanned,
        "pages": parsed["pages"] if parsed else [],
    }

    if save_json:
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{basename}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def cli_main():
    ap = argparse.ArgumentParser(description="Parse PDF into page-level JSON")
    ap.add_argument("input_pdf", help="path to input PDF")
    ap.add_argument("--out", help="output directory (default: outputs)", default="outputs")
    args = ap.parse_args()
    res = parse_pdf_to_pages(args.input_pdf, save_json=True, out_dir=args.out)
    print(f"Parsed: {res['file']}. parser_used={res['parser_used']}. needs_ocr={res['needs_ocr']}")
    print(f"Saved JSON to {os.path.join(args.out, res['basename'] + '.json')}")


if __name__ == "__main__":
    cli_main()
