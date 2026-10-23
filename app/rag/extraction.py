import logging
from pathlib import Path

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_file(file_path: str) -> str:
    """Extract and concatenate text from every page of a PDF file."""
    path = Path(file_path)
    if path.suffix.lower() != ".pdf":
        logger.warning("Skipping non-PDF file: %s", file_path)
        return ""

    try:
        reader = PdfReader(path)
        return "".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        logger.warning("Unable to extract text from PDF file: %s", file_path)
        return ""
