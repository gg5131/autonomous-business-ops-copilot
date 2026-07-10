"""Ingestion layer — document parsers, OCR, chunkers, and ingestion pipeline."""

from src.ingestion.chunker import ChunkerService
from src.ingestion.csv_parser import CSVParser
from src.ingestion.docx import DocxParser
from src.ingestion.email_parser import EmailParser
from src.ingestion.ocr import OCRService
from src.ingestion.pdf import PDFParser
from src.ingestion.pptx import PptxParser
from src.ingestion.pipeline import IngestionPipeline
