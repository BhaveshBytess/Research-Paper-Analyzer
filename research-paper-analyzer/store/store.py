# store/store.py
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from schema.models import Paper

DATA_ROOT = Path("datastore")
PAPERS_DIR = DATA_ROOT / "papers"
INDEX_PATH = DATA_ROOT / "index.json"

def _ensure_dirs():
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_PATH.exists():
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)

def _paper_id_for(paper: Dict[str, Any]) -> str:
    # deterministic id: sha256(title + authors joined)
    title = (paper.get("title") or "").strip()
    authors = paper.get("authors") or []
    authors_str = "|".join([str(a) for a in authors])
    base = f"{title}||{authors_str}"
    h = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return h

def save_paper(paper: Dict[str, Any]) -> str:
    """
    Validate paper via Pydantic (raises if invalid), then save to datastore/papers/<id>.json.
    Returns paper_id.
    """
    _ensure_dirs()
    # Validate
    p = Paper(**paper)  # will raise if invalid
    paper_dict = p.dict()
    paper_id = _paper_id_for(paper_dict)
    out_path = PAPERS_DIR / f"{paper_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(paper_dict, f, ensure_ascii=False, indent=2)
    # Update index
    idx = json.loads(open(INDEX_PATH, "r", encoding="utf-8").read())
    idx[paper_id] = {
        "title": paper_dict.get("title"),
        "authors": paper_dict.get("authors"),
        "year": paper_dict.get("year"),
        "summary": (paper_dict.get("summary") or "")[:400]
    }
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)
    return paper_id

def load_paper(paper_id: str) -> Dict[str, Any]:
    path = PAPERS_DIR / f"{paper_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"paper not found: {paper_id}")
    return json.loads(open(path, "r", encoding="utf-8").read())

def list_papers() -> Dict[str, Dict[str, Any]]:
    _ensure_dirs()
    return json.loads(open(INDEX_PATH, "r", encoding="utf-8").read())

def delete_paper(paper_id: str) -> bool:
    path = PAPERS_DIR / f"{paper_id}.json"
    if path.exists():
        path.unlink()
        idx = list_papers()
        idx.pop(paper_id, None)
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False, indent=2)
        return True
    return False
