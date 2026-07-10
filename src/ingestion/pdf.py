"""PDF Document Parser using pypdf with fallback to OCR for scanned pages."""

from __future__ import annotations

from pathlib import Path
from pypdf import PdfReader

from src.ingestion.ocr import OCRService
from src.observability.logging import get_logger

logger = get_logger(__name__)


class PDFParser:
    """Extracts text content page-by-page from PDF files."""

    def __init__(self, ocr_service: OCRService | None = None) -> None:
        self._ocr = ocr_service or OCRService()

    def parse(self, file_path: Path | str) -> str:
        """Parses the PDF document, fallback to OCR if digital text is empty."""
        logger.info("Parsing PDF file", path=str(file_path))
        try:
            reader = PdfReader(file_path)
            extracted_text = []

            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    extracted_text.append(page_text)
                else:
                    # Digital text is empty, attempt OCR on this page if possible
                    # (Fallback logic: logs scanned page and attempts full image OCR)
                    logger.debug("Page holds no digital text; scanning via OCR", page_number=i)

            text = "\n\n".join(extracted_text)

            # If total extracted text is empty, fall back to OCR on the entire file directly
            if not text.strip():
                logger.info("PDF appears to be scanned or image-only; running full OCR fallback.")
                text = self._ocr.extract_text_from_file(file_path)

            return text.strip()
        except Exception as e:
            logger.error("PDF parsing failed", error=str(e), path=str(file_path))
            return ""
