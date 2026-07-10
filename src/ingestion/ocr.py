"""Tesseract OCR — Image-to-text extraction using Pillow and pytesseract."""

from __future__ import annotations

from pathlib import Path
from PIL import Image

import pytesseract

from src.observability.logging import get_logger

logger = get_logger(__name__)


class OCRService:
    """Service utilizing Tesseract to perform optical character recognition on images."""

    @staticmethod
    def extract_text_from_file(file_path: Path | str) -> str:
        """Reads an image from path and extracts plain text."""
        logger.info("Starting OCR extraction on file", path=str(file_path))
        try:
            with Image.open(file_path) as img:
                text = pytesseract.image_to_string(img)
                logger.info("OCR completed successfully", character_count=len(text))
                return text.strip()
        except Exception as e:
            logger.error("OCR extraction failed", error=str(e), path=str(file_path))
            return ""

    @staticmethod
    def extract_text_from_bytes(image_bytes: bytes) -> str:
        """Decodes an image from bytes stream and extracts plain text."""
        import io

        logger.info("Starting OCR extraction on image stream")
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                text = pytesseract.image_to_string(img)
                logger.info("OCR completed successfully", character_count=len(text))
                return text.strip()
        except Exception as e:
            logger.error("OCR stream extraction failed", error=str(e))
            return ""
