# tests/test_ingestion.py
import os
from pathlib import Path
import tempfile
from reportlab.pdfgen import canvas
from ingestion import parser

def make_sample_pdf(path: str, text: str = "Stage 1 Parser Test: Hello PDF"):
    c = canvas.Canvas(path)
    # Simple single-line position (x, y)
    c.drawString(72, 800, text)
    c.showPage()
    c.save()

def test_parser_extracts_text(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    sample_text = "Stage 1 Parser Test: Hello PDF"
    make_sample_pdf(str(pdf_path), sample_text)
    result = parser.parse_pdf_to_pages(str(pdf_path), save_json=False)
    assert "pages" in result
    assert len(result["pages"]) >= 1
    page0 = result["pages"][0]
    # clean_text should contain the sample text
    assert sample_text in page0["clean_text"]
