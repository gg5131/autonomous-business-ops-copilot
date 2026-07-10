"""CSV Parser converting tabular rows into clear text representations."""

from __future__ import annotations

import csv
from pathlib import Path

from src.observability.logging import get_logger

logger = get_logger(__name__)


class CSVParser:
    """Parses text content from CSV and TSV spreadsheets."""

    @staticmethod
    def parse(file_path: Path | str) -> str:
        """Reads CSV and converts rows to plain text schema representation."""
        logger.info("Parsing CSV file", path=str(file_path))
        try:
            delimiter = ","
            if str(file_path).endswith(".tsv"):
                delimiter = "\t"

            with open(file_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                headers = reader.fieldnames or []
                rows = list(reader)

                extracted_text = []
                for i, row in enumerate(rows):
                    row_content = [
                        f"{col}: {val}" for col, val in row.items() if val and val.strip()
                    ]
                    if row_content:
                        extracted_text.append(f"Row {i+1}: {', '.join(row_content)}")

                return "\n".join(extracted_text).strip()
        except Exception as e:
            logger.error("CSV parsing failed", error=str(e), path=str(file_path))
            return ""
