"""PII application wrapper service delegating to configured detector interfaces."""

from __future__ import annotations

from src.security.interfaces import IPIIDetector
from src.security.pii_detectors import RegexPIIDetector


class PIIService:
    """Service encapsulating PII detection and masking capabilities."""

    def __init__(self, detector: IPIIDetector | None = None) -> None:
        # Fallback to regex-based detector if none provided (useful for direct testing)
        self._detector: IPIIDetector = detector or RegexPIIDetector()

    def has_pii(self, text: str) -> bool:
        """Check for PII content leakage."""
        return self._detector.detect_pii(text)

    def mask_pii(self, text: str) -> str:
        """Redact PII content replacing matched text with appropriate tokens."""
        return self._detector.redact_pii(text)
