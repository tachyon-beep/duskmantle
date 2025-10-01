"""Embedding helpers used during ingestion."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from functools import lru_cache

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Embedder:
    """Wrapper around sentence-transformers for configurable embeddings."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = self._load_model(model_name)
        logger.info("Embedding model %s loaded", model_name)

    @property
    def dimension(self) -> int:
        """Return the embedding dimensionality for the underlying model."""
        dimension = self._model.get_sentence_embedding_dimension()
        if dimension is None:  # pragma: no cover - defensive
            raise RuntimeError("Embedding model did not report a dimension")
        return int(dimension)

    def encode(self, texts: Iterable[str]) -> list[list[float]]:
        """Embed an iterable of texts using the configured transformer."""
        return [embedding.tolist() for embedding in self._model.encode(list(texts), convert_to_tensor=True)]

    @staticmethod
    @lru_cache(maxsize=2)
    def _load_model(model_name: str) -> SentenceTransformer:
        """Load and cache the requested sentence transformer model."""
        logger.info("Loading sentence transformer model %s", model_name)
        return SentenceTransformer(model_name)


class DummyEmbedder(Embedder):
    """Deterministic embedder for dry-runs and tests."""

    def __init__(self) -> None:  # pylint: disable=super-init-not-called
        self.model_name = "dummy"

    @property
    def dimension(self) -> int:  # pragma: no cover - trivial
        """Return the fixed dimension used by the dummy embedder."""
        return 8

    def encode(self, texts: Iterable[str]) -> list[list[float]]:
        """Produce deterministic vectors for the provided texts."""
        vectors: list[list[float]] = []
        for text in texts:
            seed = sum(ord(ch) for ch in text) or 1
            vector = [(seed % (i + 2)) / (i + 2) for i in range(self.dimension)]
            vectors.append(vector)
        return vectors
