from pathlib import Path

from app.services.extraction.docx import extract_docx
from app.services.extraction.pdf import extract_pdf
from app.services.extraction.txt import extract_txt
from app.services.extraction.types import (
    DocumentExtractionError,
    ExtractedPage,
)


def extract_document(
    file_path: Path,
) -> list[ExtractedPage]:
    """
    Automatically detect document type and extract text.
    """

    if not file_path.is_file():
        raise DocumentExtractionError(
            "Document file does not exist."
        )

    extension = file_path.suffix.lower()

    extractors = {
        ".pdf": extract_pdf,
        ".docx": extract_docx,
        ".txt": extract_txt,
    }

    extractor = extractors.get(extension)

    if extractor is None:
        raise DocumentExtractionError(
            f"Unsupported document format: {extension}"
        )

    return extractor(file_path)


__all__ = [
    "DocumentExtractionError",
    "ExtractedPage",
    "extract_document",
]