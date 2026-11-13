from dataclasses import dataclass


class DocumentExtractionError(Exception):
    """Raised when document text extraction fails."""


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    """
    Represents an extracted document content unit.

    PDF:
        page_number contains the actual 1-based PDF page.

    DOCX/TXT:
        page_number is None because reliable page
        boundaries are not available.
    """

    text: str
    page_number: int | None = None
    source_label: str | None = None