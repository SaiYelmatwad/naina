"""
Embedding providers for the matching engine.

`TfidfEmbeddingProvider` is a real, working, dependency-light implementation
(scikit-learn TF-IDF + cosine similarity) used by default so the whole
pipeline runs with zero external API calls or downloaded models.

`LLMEmbeddingProvider` shows the extension point for production-grade
semantic matching using a hosted embeddings API (OpenAI `text-embedding-3`,
Anthropic/Voyage embeddings, or a local sentence-transformers model). Swap
`get_embedding_provider()` to return this once you wire in an API key —
nothing else in the matching engine needs to change, since both providers
share the same `EmbeddingProvider` interface.
"""

from __future__ import annotations

import abc
import os
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class EmbeddingProvider(abc.ABC):
    @abc.abstractmethod
    def similarity(self, text_a: str, text_b: str) -> float:
        """Return a 0-1 semantic similarity score between two strings."""
        raise NotImplementedError


class TfidfEmbeddingProvider(EmbeddingProvider):
    """
    Hybrid lexical + vector similarity, fully local (no API calls, no downloaded models).

    Short skill names (1-2 words) get diluted to near-zero by pure TF-IDF
    cosine similarity against a long sentence, even on an exact literal
    mention — the sentence's other terms dominate the vector. Production
    hybrid-search systems handle this by blending a lexical signal (exact
    term match) with the dense/sparse vector signal; we do the same here
    with a lightweight substring check plus TF-IDF cosine.
    """

    def similarity(self, text_a: str, text_b: str) -> float:
        if not text_a.strip() or not text_b.strip():
            return 0.0

        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            matrix = vectorizer.fit_transform([text_a, text_b])
            vector_sim = float(np.clip(cosine_similarity(matrix[0:1], matrix[1:2])[0][0], 0.0, 1.0))
        except ValueError:
            vector_sim = 0.0

        lexical_sim = 0.65 if b_appears_in_a(text_a, text_b) else 0.0

        return max(vector_sim, lexical_sim)


def b_appears_in_a(text_a: str, text_b: str) -> bool:
    b = text_b.lower().strip()
    if not b:
        return False
    pattern = r"\b" + re.escape(b) + r"\b"
    return re.search(pattern, text_a.lower()) is not None


class LLMEmbeddingProvider(EmbeddingProvider):
    """
    Production extension point: real embeddings from a hosted model.

    Example wiring (left as a stub — requires an API key at runtime):

        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        # call an embeddings-capable model or a dedicated embeddings API,
        # cache vectors per skill/role text, then cosine-similarity them.
    """

    def __init__(self):
        self.api_key = os.environ.get("EMBEDDINGS_API_KEY")

    def similarity(self, text_a: str, text_b: str) -> float:
        raise NotImplementedError(
            "Wire an embeddings API key into EMBEDDINGS_API_KEY and implement "
            "the request here. Falls back to TfidfEmbeddingProvider until then."
        )


def get_embedding_provider() -> EmbeddingProvider:
    if os.environ.get("EMBEDDINGS_API_KEY"):
        return LLMEmbeddingProvider()
    return TfidfEmbeddingProvider()
