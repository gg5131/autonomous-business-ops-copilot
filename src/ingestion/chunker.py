"""Dedicated Chunking Service supporting recursive, sliding-window, and semantic chunking."""

from __future__ import annotations

import re
from typing import Any, List, Protocol

from src.observability.logging import get_logger

logger = get_logger(__name__)


class IEmbeddingService(Protocol):
    """Protocol for embedding generation to avoid circular imports with retrieval package."""

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for a single text segment."""
        ...

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of text segments in batches."""
        ...


class ChunkerService:
    """Provides methods for text division using multiple chunking strategies."""

    def __init__(self, embedding_service: IEmbeddingService | None = None) -> None:
        self._embedding_service = embedding_service

    def recursive_chunk(
        self, text: str, chunk_size: int = 500, chunk_overlap: int = 50
    ) -> List[str]:
        """Splits text recursively using paragraphs, sentences, and words to respect boundaries."""
        if not text:
            return []

        separators = ["\n\n", "\n", ". ", " ", ""]
        chunks: List[str] = []

        def _split(txt: str, max_size: int, overlap: int, seps: List[str]) -> List[str]:
            if len(txt) <= max_size:
                return [txt]

            # Choose separator
            sep = seps[0]
            for s in seps:
                if s in txt:
                    sep = s
                    break

            parts = txt.split(sep)
            current_chunk = ""
            sub_chunks: List[str] = []

            for part in parts:
                if current_chunk and len(current_chunk) + len(sep) + len(part) > max_size:
                    sub_chunks.append(current_chunk)
                    # Handle overlap (keep suffix of previous chunk)
                    current_chunk = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                if current_chunk:
                    current_chunk += sep + part
                else:
                    current_chunk = part

            if current_chunk:
                sub_chunks.append(current_chunk)

            # Recursively split any sub-chunk that remains too large
            final_chunks: List[str] = []
            for sc in sub_chunks:
                if len(sc) > max_size and len(seps) > 1:
                    final_chunks.extend(_split(sc, max_size, overlap, seps[1:]))
                else:
                    final_chunks.append(sc)

            return final_chunks

        return _split(text, chunk_size, chunk_overlap, separators)

    def sliding_window_chunk(
        self, text: str, window_size: int = 500, overlap: int = 50
    ) -> List[str]:
        """Divide text into simple sliding windows based on character length."""
        if not text:
            return []
        if window_size <= overlap:
            raise ValueError("Window size must be greater than overlap size.")

        chunks: List[str] = []
        start = 0
        while start < len(text):
            end = start + window_size
            chunks.append(text[start:end])
            start += window_size - overlap

        return chunks

    async def semantic_chunk(
        self, text: str, threshold: float = 0.82, max_chunk_len: int = 1500
    ) -> List[str]:
        """Group sentences semantically by computing cosine similarities between consecutive embeddings."""
        if not text:
            return []
        if not self._embedding_service:
            logger.warn("EmbeddingService is missing; falling back to recursive chunking.")
            return self.recursive_chunk(text)

        # Split text into sentences using simple regex
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        # Filter non-empty sentences to feed to the batch embedding generator
        non_empty_sentences = [s.strip() for s in sentences if s.strip()]
        if not non_empty_sentences:
            return []

        # Batch generate sentence embeddings
        embeddings = await self._embedding_service.get_embeddings(non_empty_sentences)

        if not embeddings:
            return [text]

        import numpy as np

        def cosine_similarity(v1: List[float], v2: List[float]) -> float:
            arr1, arr2 = np.array(v1), np.array(v2)
            denom = np.linalg.norm(arr1) * np.linalg.norm(arr2)
            if denom == 0.0:
                return 0.0
            return float(np.dot(arr1, arr2) / denom)

        chunks: List[str] = []
        current_chunk = non_empty_sentences[0]

        for i in range(1, len(non_empty_sentences)):
            sim = cosine_similarity(embeddings[i - 1], embeddings[i])
            # If similarity falls below threshold or chunk size limit is exceeded, split
            if sim < threshold or len(current_chunk) + len(non_empty_sentences[i]) > max_chunk_len:
                chunks.append(current_chunk)
                current_chunk = non_empty_sentences[i]
            else:
                current_chunk += " " + non_empty_sentences[i]

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

