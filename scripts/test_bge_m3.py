#!/usr/bin/env python
"""Quick loader to sanity-check BGE-M3 installation and device usage."""

from __future__ import annotations

import time

import torch
from FlagEmbedding import FlagModel

MODEL_NAME = "BAAI/bge-m3"


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"torch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"Active device: {torch.cuda.current_device()} -> {torch.cuda.get_device_name()}")
    print(f"Loading {MODEL_NAME} on {device}...")
    started = time.time()
    # Force single-process mode explicitly
    model = FlagModel(
        MODEL_NAME,
        use_fp16=torch.cuda.is_available(),
        device=device,
        use_multi_process=False,
    )
    elapsed = time.time() - started
    print(f"Model loaded in {elapsed:.2f}s")

    sample_text = [
        "Represent the following sentence for retrieval: How does the ingest pipeline create EXERCISES edges?",
        "Represent the following sentence for retrieval: Steps to update the symbol extractor heuristics.",
    ]
    started = time.time()
    embeddings = model.encode_single_device(
        sample_text,
        batch_size=2,
    )
    elapsed = time.time() - started
    print(f"Encoded {len(sample_text)} texts in {elapsed:.2f}s")
    print(f"Embedding shape: {len(embeddings)}, {len(embeddings[0])} dims")
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / (1024**2)
        reserved = torch.cuda.memory_reserved() / (1024**2)
        print(f"GPU memory – allocated: {allocated:.2f} MiB, reserved: {reserved:.2f} MiB")


if __name__ == "__main__":
    main()
