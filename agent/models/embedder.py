import os
import warnings
import google.generativeai as genai
from sentence_transformers import SentenceTransformer

# Suppress warnings globally
warnings.filterwarnings("ignore")

class Embedder:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.local_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.use_local = False

        if not self.api_key:
            # No API key → fallback immediately
            self.use_local = True
            return

        try:
            genai.configure(api_key=self.api_key)
            # Light model availability test
            _ = genai.GenerativeModel("models/gemini-2.5-flash")
        except Exception:
            self.use_local = True

    def embed(self, text: str):
        if not text or not text.strip():
            return []

        # Try Gemini embeddings first
        if not self.use_local:
            try:
                response = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                )
                return response["embedding"]
            except Exception:
                # Switch once to local model silently
                self.use_local = True

        # Use local embeddings as fallback
        return self.local_model.encode([text])[0].tolist()
