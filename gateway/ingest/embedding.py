"""Embedding helpers used during ingestion and search."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from functools import lru_cache
from typing import Literal

import numpy as np
import torch
from FlagEmbedding import FlagModel
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

EmbedderKind = Literal["text", "image"]

KNOWN_TEXT_DIMENSIONS = {
    "baai/bge-m3": 1024,
    "baai/bge-large-en-v1.5": 1024,
    "baai/bge-base-en-v1.5": 768,
    "baai/bge-small-en-v1.5": 384,
}


class Embedder:
    """Unified wrapper around text and image embedding backends."""

    def __init__(
        self,
        model_name: str,
        *,
        kind: EmbedderKind = "text",
        batch_size: int | None = None,
        max_length: int | None = None,
        normalize: bool = True,
    ) -> None:
        self.model_name = model_name
        self.kind = kind
        self._normalize = normalize
        self._batch_size = batch_size or (16 if kind == "text" else 8)
        self._max_length = max_length
        self._backend: Literal["flag", "sentence", "dummy"]

        if kind == "image":
            self._backend = "sentence"
            self._model = self._load_sentence_model(model_name)
            self._dimension = self._resolve_image_dimension()
            logger.info("Image embedding model %s loaded (dimension %d)", model_name, self._dimension)
            return

        if model_name.lower().startswith("baai/bge"):
            self._backend = "flag"
            use_cuda = torch.cuda.is_available()
            device = "cuda" if use_cuda else "cpu"
            try:
                self._model = self._load_flag_model(
                    model_name,
                    use_fp16=use_cuda,
                    device=device,
                )
            except OSError as exc:  # pragma: no cover - download / I/O issues bubble up
                raise RuntimeError(f"Failed to load FlagEmbedding model {model_name}: {exc}") from exc
            self._max_length = max_length or 8192
            try:
                self._model.start_multi_process_pool(target_devices=None)
            except Exception:
                pass
            model_key = model_name.lower()
            if model_key in KNOWN_TEXT_DIMENSIONS:
                self._dimension = KNOWN_TEXT_DIMENSIONS[model_key]
            else:
                self._dimension = self._resolve_text_dimension()
            logger.info(
                "Loaded FlagEmbedding model %s on %s (dimension %d)",
                model_name,
                device,
                self._dimension,
            )
        else:
            self._backend = "sentence"
            self._model = self._load_sentence_model(model_name)
            model_key = model_name.lower()
            if model_key in KNOWN_TEXT_DIMENSIONS:
                self._dimension = KNOWN_TEXT_DIMENSIONS[model_key]
            else:
                self._dimension = self._resolve_text_dimension()
            logger.info("Sentence-transformer model %s loaded (dimension %d)", model_name, self._dimension)

    @property
    def dimension(self) -> int:
        """Return the embedding dimensionality for the configured backend."""

        return self._dimension

    def encode(self, texts: Iterable[str]) -> list[list[float]]:
        """Embed a batch of inputs using the configured backend."""

        items = list(texts)
        if not items:
            return []

        if self._backend == "dummy":
            return self._encode_dummy(items)

        if self.kind == "image":
            from PIL import Image

            images = []
            for item in items:
                try:
                    with Image.open(item) as pil_image:
                        images.append(pil_image.convert("RGB"))
                except Exception as exc:  # pragma: no cover - I/O dependent
                    logger.warning("Failed to load image %s: %s", item, exc)
            if not images:
                return []
            vectors = self._model.encode(
                images,
                batch_size=self._batch_size,
                convert_to_numpy=True,
                normalize_embeddings=False,
            )
        elif self._backend == "flag":
            # FlagEmbedding's encode() path may ignore single-process hints and
            # spawn worker pools, so call the single-device helper directly.
            embeddings = self._model.encode_single_device(
                items,
                batch_size=self._batch_size,
                max_length=self._max_length,
                convert_to_numpy=True,
            )
            vectors = np.asarray(embeddings, dtype=np.float32)
        else:
            vectors = self._model.encode(
                items,
                batch_size=self._batch_size,
                convert_to_numpy=True,
                normalize_embeddings=False,
            )

        vectors = np.asarray(vectors, dtype=np.float32)
        if self._normalize:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms = np.maximum(norms, 1e-12)
            vectors = vectors / norms

        return vectors.tolist()

    def _resolve_text_dimension(self) -> int:
        model_key = self.model_name.lower()
        if model_key in KNOWN_TEXT_DIMENSIONS:
            return KNOWN_TEXT_DIMENSIONS[model_key]
        if hasattr(self._model, 'get_sentence_embedding_dimension'):
            dimension = self._model.get_sentence_embedding_dimension()
            if dimension:
                return int(dimension)
        if self._backend == "flag":
            vectors = self._model.encode_single_device(
                ['dimension probe'],
                batch_size=1,
                max_length=self._max_length or 512,
                convert_to_numpy=True,
            )
        else:
            vectors = self._model.encode(
                ['dimension probe'],
                batch_size=1,
                convert_to_numpy=True,
                normalize_embeddings=False,
            )
        return int(vectors[0].shape[-1])

    def _resolve_image_dimension(self) -> int:
        try:
            from PIL import Image
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError('Pillow is required for image embeddings') from exc
        dummy = Image.new('RGB', (2, 2), color='white')
        vectors = self._model.encode([dummy], batch_size=1, convert_to_numpy=True, normalize_embeddings=False)
        return int(vectors[0].shape[-1])

    @staticmethod
    @lru_cache(maxsize=2)
    def _load_sentence_model(model_name: str) -> SentenceTransformer:
        """Load and cache a sentence-transformer model."""

        logger.info("Loading sentence-transformer model %s", model_name)
        model = SentenceTransformer(model_name)
        if torch.cuda.is_available():  # pragma: no cover - hardware dependent
            model = model.to("cuda")
        return model

    @staticmethod
    @lru_cache(maxsize=2)
    def _load_flag_model(model_name: str, *, use_fp16: bool, device: str) -> FlagModel:
        """Load and cache a FlagEmbedding model for text embeddings."""

        logger.info(
            "Loading FlagEmbedding model %s (device=%s, fp16=%s)",
            model_name,
            device,
            use_fp16,
        )
        return FlagModel(model_name, use_fp16=use_fp16, device=device, use_multi_process=False)

    def _encode_dummy(self, texts: Iterable[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            seed = sum(ord(ch) for ch in text) or 1
            vector = [(seed % (i + 2)) / (i + 2) for i in range(self._dimension)]
            vectors.append(vector)
        return vectors


class DummyEmbedder(Embedder):
    """Deterministic embedder for dry-runs and tests."""

    def __init__(self) -> None:  # pylint: disable=super-init-not-called
        self.model_name = "dummy"
        self.kind = "text"
        self._backend = "dummy"
        self._dimension = 8
        self._normalize = False
        self._batch_size = 1
        self._max_length = None

    def encode(self, texts: Iterable[str]) -> list[list[float]]:  # pragma: no cover - simple deterministic path
        return self._encode_dummy(texts)
