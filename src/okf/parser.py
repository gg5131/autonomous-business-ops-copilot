"""OKF Markdown Parser separating frontmatter and content body."""

from __future__ import annotations

from pathlib import Path
import frontmatter

from src.observability.logging import get_logger

logger = get_logger(__name__)


class OKFParser:
    """Parses Markdown documents conforming to the Open Knowledge Format."""

    @staticmethod
    def parse_text(text: str) -> tuple[dict, str]:
        """Separates YAML frontmatter dictionary and raw body string from text."""
        try:
            post = frontmatter.loads(text)
            return post.metadata, post.content.strip()
        except Exception as e:
            logger.error("Frontmatter parsing failed", error=str(e))
            return {}, text.strip()

    @classmethod
    def parse_file(cls, file_path: Path | str) -> tuple[dict, str]:
        """Reads OKF Markdown file and parses content."""
        logger.info("Parsing OKF document", path=str(file_path))
        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                content = f.read()
            return cls.parse_text(content)
        except Exception as e:
            logger.error("Failed to read OKF file", error=str(e), path=str(file_path))
            return {}, ""
