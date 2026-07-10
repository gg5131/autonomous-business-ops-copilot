"""OKF Bundle Builder validating schema configurations."""

from __future__ import annotations

from pathlib import Path

from src.okf.parser import OKFParser
from src.okf.schemas import OKFBundle, OKFMetadata
from src.okf.versioning import OKFVersioner
from src.observability.logging import get_logger

logger = get_logger(__name__)


class OKFBundleBuilder:
    """Builds and validates OKF bundles from files or raw content strings."""

    @staticmethod
    def build_from_text(text: str) -> OKFBundle:
        """Parses raw text, validates schemas, and builds the bundle."""
        meta_dict, body_content = OKFParser.parse_text(text)

        # Validate metadata schema
        metadata = OKFMetadata.model_validate(meta_dict)

        # Compute SHA-256 hash of content body
        sha256 = OKFVersioner.compute_sha256(body_content)

        return OKFBundle(
            metadata=metadata,
            content=body_content,
            sha256_hash=sha256,
        )

    @classmethod
    def build_from_file(cls, file_path: Path | str) -> OKFBundle:
        """Reads document path, validates schemas, and builds the bundle."""
        logger.info("Building OKF bundle from file", path=str(file_path))
        with open(file_path, mode="r", encoding="utf-8") as f:
            text = f.read()

        return cls.build_from_text(text)
