"""
Embeddings factory module.
Provides Google Gemini embeddings when LLM_API_KEY is configured,
or a local fallback embedding generator for offline testing and setup.
"""
import hashlib
import math
from typing import List
from langchain_core.embeddings import Embeddings
from app.config import settings


class LocalFallbackEmbeddings(Embeddings):
    """
    Deterministic offline embedding model (dimension = 128).
    Used as a fallback when no Google Gemini API key is configured.
    Ensures vector search and testing work without API keys.
    """
    def __init__(self, dimension: int = 128):
        self.dimension = dimension

    def _embed_single_text(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        words = text.lower().split()
        if not words:
            return vector

        for word in words:
            # Hash word into bucket
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            index = h % self.dimension
            vector[index] += 1.0

        # L2 Normalize
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_single_text(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_single_text(text)


def get_embedding_function() -> Embeddings:
    """
    Returns GoogleGenerativeAIEmbeddings if LLM_API_KEY is present,
    otherwise returns LocalFallbackEmbeddings.
    """
    api_key = settings.LLM_API_KEY.strip() if settings.LLM_API_KEY else ""

    # Check if a genuine API key is present
    if api_key and api_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=api_key,
            )
        except Exception as e:
            print(f"Warning: Failed to initialize Google Generative AI embeddings ({e}). Falling back to local offline embeddings.")
            return LocalFallbackEmbeddings()
    else:
        return LocalFallbackEmbeddings()
