import os
import pickle
import math
from typing import List
from sentence_transformers import SentenceTransformer

class ResumeMemory:
    def __init__(self, db_path: str = None):
        """
        ResumeMemory stores embeddings and text chunks for a single resume.
        db_path: folder where vectors.pkl will be saved/loaded.
        """
        self.db_path = db_path or os.path.join("data", "vector_dbs", "default")
        os.makedirs(self.db_path, exist_ok=True)

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self.text_chunks: List[str] = []
        self.embeddings: List[List[float]] = []

        self._load_vectors()

    # ---------- persistence ----------
    def _vectors_file(self) -> str:
        return os.path.join(self.db_path, "vectors.pkl")

    def _save_vectors(self):
        data = {
            "texts": self.text_chunks,
            "embeddings": self.embeddings
        }
        with open(self._vectors_file(), "wb") as f:
            pickle.dump(data, f)

    def _load_vectors(self):
        path = self._vectors_file()
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    data = pickle.load(f)
                    self.text_chunks = data.get("texts", []) or []
                    self.embeddings = data.get("embeddings", []) or []
            except Exception:
                # ignore corrupted file and start fresh
                self.text_chunks = []
                self.embeddings = []

    # ---------- storage & indexing ----------
    def store_resume(self, text: str, resume_id: str = "resume"):
        """
        Chunk the resume text, compute embeddings, and persist them.
        Overwrites any existing vectors in this db_path.
        """
        if not text or not text.strip():
            return

        chunks = [text[i:i+1000].strip() for i in range(0, len(text), 1000) if text[i:i+1000].strip()]
        self.text_chunks = chunks

        emb_matrix = self.model.encode(chunks, show_progress_bar=False)
        self.embeddings = [e.tolist() if hasattr(e, "tolist") else list(e) for e in emb_matrix]

        # persist
        self._save_vectors()

    # ---------- retrieval ----------
    def _cosine(self, a: List[float], b: List[float]) -> float:
        # safe cosine similarity
        dot = 0.0
        na = 0.0
        nb = 0.0
        for x, y in zip(a, b):
            dot += x * y
            na += x * x
            nb += y * y
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (math.sqrt(na) * math.sqrt(nb))

    def get_top_chunks(self, query: str, top_k: int = 3) -> List[str]:
        """
        Return top_k text chunks most relevant to the query.
        If no embeddings exist, returns an empty list.
        """
        if not self.embeddings or not self.text_chunks:
            return []

        q_emb = self.model.encode([query], show_progress_bar=False)[0].tolist()

        scores = []
        for emb in self.embeddings:
            try:
                score = self._cosine(emb, q_emb)
            except Exception:
                score = 0.0
            scores.append(score)

        idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [self.text_chunks[i] for i in idxs]

    def query(self, query_text: str, top_k: int = 3):
        return self.get_top_chunks(query_text, top_k=top_k)

    # ---------- utilities ----------
    def has_resume(self) -> bool:
        return bool(self.text_chunks and self.embeddings)
