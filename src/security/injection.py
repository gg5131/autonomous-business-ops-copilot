"""Heuristic prompt injection detector implementing safety filters."""

from __future__ import annotations

import re


class PromptInjectionDetector:
    """Detects instruction overrides, system bypasses, and jailbreak commands."""

    def __init__(self) -> None:
        # Precompile common injection phrases/patterns
        self._indicators = [
            re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
            re.compile(r"system\s+override", re.IGNORECASE),
            re.compile(r"you\s+are\s+now\s+a\s+", re.IGNORECASE),
            re.compile(r"bypass\s+restrictions", re.IGNORECASE),
            re.compile(r"dan\s+mode", re.IGNORECASE),
            re.compile(r"do\s+anything\s+now", re.IGNORECASE),
            re.compile(r"ignore\s+safety\s+guidelines", re.IGNORECASE),
        ]

    def has_injection(self, text: str) -> bool:
        """Analyze text against safety indicators. Return True if injection is detected."""
        if not text:
            return False

        for indicator in self._indicators:
            if indicator.search(text):
                return True
        return False
