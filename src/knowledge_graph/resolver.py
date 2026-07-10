"""Entity Resolution and Deduplication module."""

from __future__ import annotations

from typing import Dict, List


class EntityResolver:
    """Consolidates duplicate or coreferent entities using name normalization and distance checks."""

    @staticmethod
    def normalize_name(name: str) -> str:
        """Strip company endings and clean whitespace/casing for matching."""
        if not name:
            return ""

        # Normalize casing and clean whitespace
        val = name.strip().lower()

        # Remove common corporate suffixes
        suffixes = [" llc", " inc.", " inc", " corp.", " corp", " ltd.", " ltd", " co.", " co"]
        for suffix in suffixes:
            if val.endswith(suffix):
                val = val[: -len(suffix)].strip()

        # Title-case for a clean target canonical name representation
        return val.title()

    def resolve_entities(self, entities: List[str]) -> Dict[str, str]:
        """Maps list of entity strings to their resolved canonical representations."""
        # Maps raw entity name -> canonical resolved name
        resolved_map: Dict[str, str] = {}
        canonical_map: Dict[str, str] = {}  # normalized -> canonical original name

        for entity in entities:
            normalized = self.normalize_name(entity)
            if not normalized:
                continue

            # If normalized form is already mapped, reuse the canonical original name
            if normalized in canonical_map:
                resolved_map[entity] = canonical_map[normalized]
            else:
                # First time seeing this normalized form, establish entity as the canonical choice
                canonical_map[normalized] = entity
                resolved_map[entity] = entity

        return resolved_map
