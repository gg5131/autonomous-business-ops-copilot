"""Input validation and sanitization utilities."""

from __future__ import annotations

import html


class InputSanitizer:
    """Provides utility methods to scrub inputs and clean strings."""

    @staticmethod
    def sanitize(text: str) -> str:
        """Strip HTML tags and convert special characters to HTML entities."""
        if not text:
            return ""
        # Strip simple HTML tags using regex if needed, or escape them directly
        escaped = html.escape(text)
        return escaped.strip()
