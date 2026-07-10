"""Embedding Service with pluggable SQLite database disk caching and batching."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from sentence_transformers import SentenceTransformer

from configs.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class IEmbeddingCache(ABC):
    """Abstract interface for pluggable embedding vector caching."""

    @abstractmethod
    def get(self, text: str, model_name: str) -> Optional[List[float]]:
        """Retrieve embedding from cache if it exists."""

    @abstractmethod
    def set(self, text: str, model_name: str, embedding: List[float]) -> None:
        """Store embedding in cache."""


class SQLiteEmbeddingCache(IEmbeddingCache):
    """SQLite/disk-backed persistent embedding cache."""

    def __init__(self, db_path: str = "./data/embedding_cache.db") -> None:
        self.db_path = db_path
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings (
                    text_hash TEXT,
                    model_name TEXT,
                    embedding TEXT,
                    PRIMARY KEY (text_hash, model_name)
                )
                """
            )
            conn.commit()

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str, model_name: str) -> Optional[List[float]]:
        h = self._hash(text)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT embedding FROM embeddings WHERE text_hash = ? AND model_name = ?",
                    (h, model_name),
                )
                row = cursor.fetchone()
                if row:
                    return list(json.loads(row[0]))
        except Exception as e:
            logger.error("Failed to query embedding cache", error=str(e))
        return None

    def set(self, text: str, model_name: str, embedding: List[float]) -> None:
        h = self._hash(text)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO embeddings (text_hash, model_name, embedding) VALUES (?, ?, ?)",
                    (h, model_name, json.dumps(embedding)),
                )
                conn.commit()
        except Exception as e:
            logger.error("Failed to write embedding cache", error=str(e))


class EmbeddingService:
    """Configurable service generating dense vectors using Sentence Transformers with caching."""

    def __init__(
        self,
        model_name: str | None = None,
        cache: IEmbeddingCache | None = None,
    ) -> None:
        self.model_name = model_name or settings.embedding.model
        # Pluggable cache: defaults to SQLite/disk cache
        self.cache = cache or SQLiteEmbeddingCache()
        logger.info("Initializing SentenceTransformer model", model=self.model_name)
        self._model = SentenceTransformer(self.model_name)

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for a single text segment (cached)."""
        if not text:
            return []

        # Check cache first
        cached = self.cache.get(text, self.model_name)
        if cached is not None:
            return cached

        # Generate embedding
        logger.debug("Generating single text embedding (cache miss)")
        embeddings = self._model.encode([text], batch_size=1, show_progress_bar=False)
        vector = [float(val) for val in embeddings[0]]

        # Write to cache
        self.cache.set(text, self.model_name, vector)
        return vector

    async def get_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embedding vectors for a list of text segments, checking cache and batching."""
        if not texts:
            return []

        results: List[Optional[List[float]]] = [None] * len(texts)
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []

        # 1. Check cache for all texts
        for i, text in enumerate(texts):
            cached = self.cache.get(text, self.model_name)
            if cached is not None:
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # 2. Encode remaining texts in batches
        if uncached_texts:
            logger.info("Generating batch embeddings (cache miss)", count=len(uncached_texts))
            encoded = self._model.encode(
                uncached_texts,
                batch_size=batch_size,
                show_progress_bar=False,
            )

            # Store in cache and assign to final results list
            for i, idx in enumerate(uncached_indices):
                vector = [float(val) for val in encoded[i]]
                self.cache.set(uncached_texts[i], self.model_name, vector)
                results[idx] = vector

        # Filter out None types (guaranteed to be resolved)
        final_vectors: List[List[float]] = [res for res in results if res is not None]
        return final_vectors
