"""Ingestion Orchestration Pipeline routing documents to appropriate parser engines."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from src.ingestion.chunker import ChunkerService
from src.ingestion.csv_parser import CSVParser
from src.ingestion.docx import DocxParser
from src.ingestion.email_parser import EmailParser
from src.ingestion.ocr import OCRService
from src.ingestion.pdf import PDFParser
from src.ingestion.pptx import PptxParser
from src.observability.logging import get_logger

logger = get_logger(__name__)


class IngestionPipeline:
    """Ingestion controller discovering and executing file parsers and chunking."""

    def __init__(
        self,
        chunker: ChunkerService | None = None,
        ocr: OCRService | None = None,
        pdf: PDFParser | None = None,
        docx: DocxParser | None = None,
        pptx: PptxParser | None = None,
        csv_p: CSVParser | None = None,
        email_p: EmailParser | None = None,
    ) -> None:
        self.chunker = chunker or ChunkerService()
        self._ocr = ocr or OCRService()
        self._pdf = pdf or PDFParser(self._ocr)
        self._docx = docx or DocxParser()
        self._pptx = pptx or PptxParser()
        self._csv = csv_p or CSVParser()
        self._email = email_p or EmailParser()

    async def parse_file(self, file_path: Path | str) -> str:
        """Parse file by selecting the parser corresponding to its extension."""
        path = Path(file_path)
        ext = path.suffix.lower()

        logger.info("Routing file to parser", extension=ext, path=str(path))

        if ext == ".pdf":
            return self._pdf.parse(path)
        elif ext in [".docx", ".doc"]:
            return self._docx.parse(path)
        elif ext == ".pptx":
            return self._pptx.parse(path)
        elif ext in [".csv", ".tsv"]:
            return self._csv.parse(path)
        elif ext in [".eml", ".msg"]:
            return self._email.parse(path)
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            return self._ocr.extract_text_from_file(path)
        elif ext in [".txt", ".md"]:
            try:
                with open(path, mode="r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                logger.error("Text file read failed", error=str(e), path=str(path))
                return ""
        else:
            logger.warn("Unsupported file extension. Ingestion skipped.", extension=ext)
            return ""

    async def ingest_document(
        self,
        file_path: Path | str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        strategy: str = "recursive",
    ) -> List[str]:
        """Runs the parsing and chunking pipeline on a single document."""
        text = await self.parse_file(file_path)
        if not text:
            logger.warn("Ingested document produced empty content.", path=str(file_path))
            return []

        logger.info("Starting chunking execution", strategy=strategy, character_count=len(text))

        if strategy == "semantic":
            return await self.chunker.semantic_chunk(text)
        elif strategy == "sliding":
            return self.chunker.sliding_window_chunk(text, chunk_size, chunk_overlap)
        else:
            return self.chunker.recursive_chunk(text, chunk_size, chunk_overlap)
