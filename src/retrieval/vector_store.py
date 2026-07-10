"""ChromaDB Integration Layer for dense vector searches with metadata filtering."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from configs.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ChromaVectorStore:
    """Wrapper managing vector inserts and metadata-filtered collection queries in ChromaDB."""

    def __init__(self, collection_name: str | None = None) -> None:
        self.collection_name = collection_name or settings.chroma.collection
        logger.info("Initializing ChromaDB HTTP client", host=settings.chroma.host, port=settings.chroma.port)

        # Connect to ChromaDB container using HTTP client settings
        self._client = chromadb.HttpClient(
            host=settings.chroma.host,
            port=settings.chroma.port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """Upsert text segments and their dense vectors with metadata mapping into ChromaDB."""
        if not chunks:
            return

        logger.info("Adding chunks to ChromaDB", count=len(chunks), collection=self.collection_name)
        try:
            self._collection.upsert(
                documents=chunks,
                embeddings=embeddings,  # type: ignore
                metadatas=metadatas,  # type: ignore
                ids=ids,
            )
            logger.info("Chunks successfully upserted to ChromaDB.")
        except Exception as e:
            logger.error("ChromaDB upsert failed", error=str(e))
            raise

    def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query collection using similarity vector search combined with metadata constraints."""
        logger.info("Searching ChromaDB collection", limit=limit, has_filters=filters is not None)

        where_clause: Dict[str, Any] = {}

        if filters:
            # Build valid metadata filtering map for ChromaDB
            # Supported filters: department, doc_type, tags, language, author, date, confidence, source
            valid_keys = [
                "department",
                "doc_type",
                "tags",
                "language",
                "author",
                "date",
                "confidence",
                "source",
            ]
            filter_conditions: List[Dict[str, Any]] = []

            for key, val in filters.items():
                if key in valid_keys and val is not None:
                    # Chroma expects individual constraints or $and/$or blocks
                    if isinstance(val, list):
                        # Tag check contains fallback
                        filter_conditions.append({key: {"$in": val}})
                    else:
                        filter_conditions.append({key: {"$eq": val}})

            if len(filter_conditions) == 1:
                where_clause = filter_conditions[0]
            elif len(filter_conditions) > 1:
                where_clause = {"$and": filter_conditions}

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],  # type: ignore
                n_results=limit,
                where=where_clause if where_clause else None,  # type: ignore
            )

            formatted_results: List[Dict[str, Any]] = []
            if results and results["documents"]:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else []
                distances = results["distances"][0] if results["distances"] else []
                ids = results["ids"][0]

                for idx, doc in enumerate(documents):
                    # Convert distance to similarity score
                    dist = distances[idx] if idx < len(distances) else 1.0
                    similarity = float(1.0 - dist)

                    formatted_results.append(
                        {
                            "id": ids[idx],
                            "content": doc,
                            "metadata": metadatas[idx] if idx < len(metadatas) else {},
                            "score": similarity,
                        }
                    )

            logger.info("ChromaDB search completed", result_count=len(formatted_results))
            return formatted_results
        except Exception as e:
            logger.error("ChromaDB search query failed", error=str(e))
            return []
