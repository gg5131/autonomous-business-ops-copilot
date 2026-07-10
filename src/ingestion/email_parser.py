"""Email Parser extracting content from .eml files."""

from __future__ import annotations

import email
from email.message import Message
from pathlib import Path

from src.observability.logging import get_logger

logger = get_logger(__name__)


class EmailParser:
    """Parses text headers and HTML/plain body from email message packages."""

    @staticmethod
    def parse(file_path: Path | str) -> str:
        """Extracts text content from .eml file."""
        logger.info("Parsing email file", path=str(file_path))
        try:
            with open(file_path, mode="rb") as f:
                msg = email.message_from_binary_file(f)

            headers = []
            for header in ["From", "To", "Subject", "Date"]:
                val = msg.get(header)
                if val:
                    headers.append(f"{header}: {val}")

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disp = str(part.get("Content-Disposition"))

                    if content_type == "text/plain" and "attachment" not in content_disp:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")

            full_text = "\n".join(headers) + "\n\nBody:\n" + body
            return full_text.strip()
        except Exception as e:
            logger.error("Email parsing failed", error=str(e), path=str(file_path))
            return ""
