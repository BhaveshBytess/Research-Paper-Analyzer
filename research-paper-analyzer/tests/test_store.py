# tests/test_store.py
import tempfile
import shutil
import os
from pathlib import Path
from store.store import save_paper, load_paper, list_papers
from store.embeddings import EmbeddingModel, EmbeddingIndex
import json

SAMPLE_PAPERS = [
    {
        "title": "Paper A — Cats",
        "authors": ["Author X"],
        "year": 2021,
        "summary": "This paper studies cat detectors and achieves 90% accuracy on SmallCatSet.",
        "evidence": {"title":[{"page":1,"snippet":"Paper A — Cats"}]}
    },
    {
        "title": "Paper B — Dogs",
        "authors": ["Author Y"],
        "year": 2022,
        "summary": "This paper studies dog detectors and achieves 88% accuracy on SmallDogSet.",
        "evidence": {"title":[{"page":1,"snippet":"Paper B — Dogs"}]}
    }
]

def test_store_and_search(tmp_path, monkeypatch):
    # Redirect datastore to a temp directory by changing DATA_ROOT env var
    # The store module uses datastore/ relative path; we change CWD to tmp_path to isolate
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Save sample papers
        ids = []
        for p in SAMPLE_PAPERS:
            pid = save_paper(p)
            ids.append(pid)
        idx = list_papers()
        assert len(idx) == 2

        # Build embedding index (mock mode)
        model = EmbeddingModel(use_mock=True, dim=64)
        emb_index = EmbeddingIndex(model=model, dim=64, use_faiss=False)
        # Add each paper embedding using summary text
        for pid in ids:
            paper = load_paper(pid)
            text = (paper.get("summary") or "") + " " + (paper.get("title") or "")
            emb_index.add(pid, text)
        # Build index
        emb_index.build()
        # Search using the summary of Paper A
        q = SAMPLE_PAPERS[0]["summary"]
        results = emb_index.search(q, top_k=2)
        # Top hit must be the paper A id
        top_id, dist = results[0]
        assert top_id == ids[0], f"Expected top id {ids[0]}, got {top_id}"
    finally:
        os.chdir(cwd)
