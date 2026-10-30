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


class ResilientEmbeddings(Embeddings):
    """
    Wraps primary embeddings (Google Generative AI) with fallback to LocalFallbackEmbeddings
    if remote API calls fail (network errors, quota limits, invalid keys).
    Ensures vector search and question answering remain operational during transient provider issues.
    """
    def __init__(self, primary: Embeddings, fallback: Embeddings):
        self.primary = primary
        self.fallback = fallback

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            return self.primary.embed_documents(texts)
        except Exception as e:
            print(f"Notice: Primary embeddings error ({e}). Using offline local fallback.")
            return self.fallback.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        try:
            return self.primary.embed_query(text)
        except Exception as e:
            print(f"Notice: Primary embedding query error ({e}). Using offline local fallback.")
            return self.fallback.embed_query(text)


def get_embedding_function() -> Embeddings:
    """
    Returns ResilientEmbeddings wrapping GoogleGenerativeAIEmbeddings when LLM_API_KEY is present,
    otherwise returns LocalFallbackEmbeddings.
    """
    api_key = settings.LLM_API_KEY.strip() if settings.LLM_API_KEY else ""

    # Check if a genuine API key is present
    if api_key and api_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            primary = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=api_key,
            )
            return ResilientEmbeddings(primary=primary, fallback=LocalFallbackEmbeddings())
        except Exception as e:
            print(f"Warning: Failed to initialize Google Generative AI embeddings ({e}). Falling back to local offline embeddings.")
            return LocalFallbackEmbeddings()
    else:
        return LocalFallbackEmbeddings()
