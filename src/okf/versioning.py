"""SHA-256 based content hashing and incremental ingestion checks."""

from __future__ import annotations

import hashlib
from pathlib import Path


class OKFVersioner:
    """Computes SHA-256 hashes to track file versioning and prevent duplicate ingestion."""

    @staticmethod
    def compute_sha256(text: str) -> str:
        """Calculate SHA-256 checksum for a string."""
        if not text:
            return ""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def compute_file_sha256(cls, file_path: Path | str) -> str:
        """Read file in chunks and calculate SHA-256 checksum."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, mode="rb") as f:
                # Read in 64kb blocks
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return ""
