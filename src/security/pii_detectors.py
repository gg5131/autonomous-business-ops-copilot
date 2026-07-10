"""Regex-based PII Detector implementation of IPIIDetector."""

from __future__ import annotations

import re
from typing import Dict

from src.security.interfaces import IPIIDetector


class RegexPIIDetector(IPIIDetector):
    """Detects and redacts common PII elements using compiled regular expressions."""

    def __init__(self) -> None:
        # Pre-compile regex patterns for performance
        self._patterns: Dict[str, re.Pattern[str]] = {
            "EMAIL": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
            "PHONE": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
            "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "CREDIT_CARD": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        }

    def detect_pii(self, text: str) -> bool:
        """Return True if any pattern finds a match in the target text."""
        if not text:
            return False

        for pattern in self._patterns.values():
            if pattern.search(text):
                return True
        return False

    def redact_pii(self, text: str) -> str:
        """Redact matched PII components substituting with bracketed placeholders."""
        if not text:
            return ""

        redacted = text
        for label, pattern in self._patterns.items():
            redacted = pattern.sub(f"[{label}_REDACTED]", redacted)
        return redacted
