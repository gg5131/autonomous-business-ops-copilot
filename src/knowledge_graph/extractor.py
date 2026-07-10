"""Gemini-powered Entity and Relationship extractor enforcing Neo4j Graph schemas."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


import httpx

from configs.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

VALID_NODE_TYPES = [
    "Document",
    "Chunk",
    "Entity",
    "Policy",
    "Department",
    "Person",
    "Product",
    "Process",
]

VALID_REL_TYPES = [
    "MENTIONS",
    "BELONGS_TO",
    "RELATED_TO",
    "REFERENCES",
    "DERIVED_FROM",
    "VERSION_OF",
]


class GraphExtractor:
    """Extracts schema-conforming graph structures with confidence values from text."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.gemini.api_key
        self.model = settings.gemini.model_default

    async def extract_graph(
        self, text: str, source_name: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Parse text and return lists of extracted nodes and relationships with metadata."""
        logger.info("Extracting graph nodes and relationships", source=source_name)

        if not text or not text.strip():
            return {"nodes": [], "relationships": []}

        if not self.api_key:
            return self._extract_fallback(text, source_name)

        prompt = (
            "Analyze the text below and extract knowledge entities and relationships matching the target schemas.\n\n"
            f"Allowed Node Label Types: {VALID_NODE_TYPES}\n"
            f"Allowed Relationship Types: {VALID_REL_TYPES}\n\n"
            "Target output JSON structure:\n"
            "{\n"
            '  "nodes": [\n'
            '    {"name": "entity name", "type": "NodeLabelType", "properties": {"description": "brief explanation"}, "confidence": 0.9}\n'
            "  ],\n"
            '  "relationships": [\n'
            '    {"source_node": "entity name", "source_type": "NodeLabelType", "target_node": "another name", "target_type": "NodeLabelType", "type": "REL_TYPE", "confidence": 0.85}\n'
            "  ]\n"
            "}\n\n"
            f"Source text:\n\"\"\"\n{text}\n\"\"\"\n\n"
            "Respond ONLY with a valid JSON payload matching the target output structure. "
            "Do not add markdown formatting or conversational blocks."
        )

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json",
                },
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    extracted = json.loads(raw_text)
                    return self._validate_and_format(extracted, source_name)
                else:
                    logger.error("Gemini extractor request failed", code=response.status_code)
                    return self._extract_fallback(text, source_name)
        except Exception as e:
            logger.warn("Gemini graph extraction failed; returning fallback parses.", error=str(e))
            return self._extract_fallback(text, source_name)

    def _validate_and_format(
        self, raw_data: Dict[str, Any], source_name: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Validate nodes/relations conform to schema types, injecting source & timestamps."""
        timestamp = datetime.utcnow().isoformat()

        clean_nodes: List[Dict[str, Any]] = []
        clean_rels: List[Dict[str, Any]] = []

        # Validate nodes
        for node in raw_data.get("nodes", []):
            label = node.get("type")
            if label in VALID_NODE_TYPES:
                clean_nodes.append(
                    {
                        "name": str(node.get("name")).strip(),
                        "type": label,
                        "properties": node.get("properties") or {},
                        "confidence": float(node.get("confidence", 1.0)),
                        "extraction_source": source_name,
                        "extraction_timestamp": timestamp,
                    }
                )

        # Validate relationships
        for rel in raw_data.get("relationships", []):
            rel_type = rel.get("type")
            if (
                rel_type in VALID_REL_TYPES
                and rel.get("source_type") in VALID_NODE_TYPES
                and rel.get("target_type") in VALID_NODE_TYPES
            ):
                clean_rels.append(
                    {
                        "source_node": str(rel.get("source_node")).strip(),
                        "source_type": rel.get("source_type"),
                        "target_node": str(rel.get("target_node")).strip(),
                        "target_type": rel.get("target_type"),
                        "type": rel_type,
                        "confidence": float(rel.get("confidence", 1.0)),
                        "extraction_source": source_name,
                        "extraction_timestamp": timestamp,
                    }
                )

        return {"nodes": clean_nodes, "relationships": clean_rels}

    def _extract_fallback(self, text: str, source_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """Rule-based regex fallback extracting capitalized noun phrases as Entity entities."""
        logger.info("Executing rule-based graph extraction fallback")
        timestamp = datetime.utcnow().isoformat()

        # Simple regex to find potential Proper Nouns (capitalized word sequences)
        candidates = list(set(re.findall(r"\b[A-Z][a-zA-Z0-9_]{2,}(?:\s+[A-Z][a-zA-Z0-9_]{2,})*\b", text)))

        nodes: List[Dict[str, Any]] = []
        relationships: List[Dict[str, Any]] = []

        for candidate in candidates[:10]:  # Limit candidates
            nodes.append(
                {
                    "name": candidate,
                    "type": "Entity",
                    "properties": {"description": f"Extracted from {source_name}."},
                    "confidence": 0.7,
                    "extraction_source": source_name,
                    "extraction_timestamp": timestamp,
                }
            )

        # Connect consecutive candidates
        for i in range(1, len(nodes)):
            relationships.append(
                {
                    "source_node": nodes[i - 1]["name"],
                    "source_type": "Entity",
                    "target_node": nodes[i]["name"],
                    "target_type": "Entity",
                    "type": "RELATED_TO",
                    "confidence": 0.5,
                    "extraction_source": source_name,
                    "extraction_timestamp": timestamp,
                }
            )

        return {"nodes": nodes, "relationships": relationships}
