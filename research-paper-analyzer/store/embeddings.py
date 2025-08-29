# store/embeddings.py
import os
import json
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from store.store import PAPERS_DIR, DATA_ROOT
import hashlib

# Attempt to import faiss if available
try:
    import faiss
    _HAS_FAISS = True
except Exception:
    _HAS_FAISS = False

# Attempt to import sentence-transformers only when requested
try:
    from sentence_transformers import SentenceTransformer
    _HAS_S2 = True
except Exception:
    _HAS_S2 = False

# fallback sklearn neighbor
try:
    from sklearn.neighbors import NearestNeighbors
    _HAS_SK = True
except Exception:
    _HAS_SK = False

EMBED_DIR = DATA_ROOT / "embeddings"
IDMAP_PATH = EMBED_DIR / "id_to_idx.json"
EMBED_MATRIX_PATH = EMBED_DIR / "embeddings.npy"

def _ensure_embed_dir():
    EMBED_DIR.mkdir(parents=True, exist_ok=True)

class EmbeddingModel:
    """
    Wrapper that either uses a real SentenceTransformer or a deterministic mock embedder.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_mock: bool = True, dim: int = 384):
        self.use_mock = use_mock
        self.dim = dim
        self.model_name = model_name
        self._model = None
        if not use_mock:
            if not _HAS_S2:
                raise RuntimeError("sentence-transformers not installed. Install or use use_mock=True.")
            self._model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> np.ndarray:
        if self.use_mock:
            # deterministic pseudo-embeddings based on hash seed
            vecs = []
            for t in texts:
                h = hashlib.sha256(t.encode("utf-8")).digest()
                seed = int.from_bytes(h[:8], "big") % (2**32 - 1)
                rng = np.random.RandomState(seed)
                v = rng.rand(self.dim).astype(np.float32)
                # normalize
                v = v / (np.linalg.norm(v) + 1e-9)
                vecs.append(v)
            return np.vstack(vecs)
        else:
            emb = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            # ensure float32
            if emb.dtype != np.float32:
                emb = emb.astype(np.float32)
            return emb

class EmbeddingIndex:
    def __init__(self, model: EmbeddingModel, dim: Optional[int] = None, use_faiss: bool = True):
        self.model = model
        self.dim = dim or model.dim
        self.use_faiss = use_faiss and _HAS_FAISS
        _ensure_embed_dir()
        # in-memory arrays
        self.id_to_idx = {}  # paper_id -> idx
        self.idx_to_id = []
        self.embeddings = None  # numpy array shape (n, dim)
        self._faiss_index = None
        self._sk_nn = None

    def _save_aux(self):
        _ensure_embed_dir()
        # id map
        with open(IDMAP_PATH, "w", encoding="utf-8") as f:
            json.dump(self.id_to_idx, f, ensure_ascii=False, indent=2)
        # embeddings
        if self.embeddings is not None:
            np.save(EMBED_MATRIX_PATH, self.embeddings)

    def _load_aux(self):
        if IDMAP_PATH.exists():
            self.id_to_idx = json.loads(open(IDMAP_PATH, "r", encoding="utf-8").read())
            # build idx_to_id
            # id_to_idx is paper_id -> idx
            # create list where idx -> id
            maxidx = max(self.id_to_idx.values()) if self.id_to_idx else -1
            self.idx_to_id = [None] * (maxidx + 1)
            for pid, idx in self.id_to_idx.items():
                self.idx_to_id[idx] = pid
        if EMBED_MATRIX_PATH.exists():
            self.embeddings = np.load(str(EMBED_MATRIX_PATH))

    def add(self, paper_id: str, text: str):
        """
        Compute embedding for text and append to in-memory arrays.
        """
        emb = self.model.embed([text])[0]
        if self.embeddings is None:
            self.embeddings = np.vstack([emb])
            self.idx_to_id = [paper_id]
            self.id_to_idx = {paper_id: 0}
        else:
            idx = self.embeddings.shape[0]
            self.embeddings = np.vstack([self.embeddings, emb])
            self.idx_to_id.append(paper_id)
            self.id_to_idx[paper_id] = idx
        # Save aux for persistence
        self._save_aux()

    def build(self):
        """
        Build ANN structure (FAISS if available else sklearn).
        """
        if self.embeddings is None or self.embeddings.shape[0] == 0:
            raise RuntimeError("No embeddings to build index from.")
        if self.use_faiss:
            # FAISS IndexFlatL2
            self._faiss_index = faiss.IndexFlatL2(self.dim)
            self._faiss_index.add(self.embeddings.astype(np.float32))
        else:
            if not _HAS_SK:
                raise RuntimeError("sklearn not available for fallback nearest neighbors.")
            self._sk_nn = NearestNeighbors(metric="euclidean", algorithm="auto")
            self._sk_nn.fit(self.embeddings)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Search and return list of (paper_id, score) where score is distance (lower = closer).
        """
        qv = self.model.embed([query])[0].astype(np.float32)
        if self.use_faiss and self._faiss_index is not None:
            D, I = self._faiss_index.search(np.expand_dims(qv, axis=0), top_k)
            D = D[0].tolist()
            I = I[0].tolist()
            results = []
            for dist, idx in zip(D, I):
                pid = self.idx_to_id[idx] if idx < len(self.idx_to_id) else None
                results.append((pid, float(dist)))
            return results
        else:
            if self._sk_nn is None:
                # build on the fly
                self.build()
            D, I = self._sk_nn.kneighbors([qv], n_neighbors=min(top_k, len(self.idx_to_id)))
            D = D[0].tolist()
            I = I[0].tolist()
            results = []
            for dist, idx in zip(D, I):
                pid = self.idx_to_id[idx] if idx < len(self.idx_to_id) else None
                results.append((pid, float(dist)))
            return results

    def save(self):
        self._save_aux()
        # If FAISS index present, save it
        if self.use_faiss and self._faiss_index is not None:
            faiss.write_index(self._faiss_index, str(EMBED_DIR / "faiss.index"))

    def load(self):
        self._load_aux()
        # load faiss index if present
        if self.use_faiss and (EMBED_DIR / "faiss.index").exists():
            self._faiss_index = faiss.read_index(str(EMBED_DIR / "faiss.index"))
        else:
            # else we'll build when needed
            self._faiss_index = None
