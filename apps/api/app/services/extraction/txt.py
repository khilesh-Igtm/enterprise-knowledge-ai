from pathlib import Path

from app.services.extraction.types import (
    DocumentExtractionError,
    ExtractedPage,
)


def extract_txt(file_path: Path) -> list[ExtractedPage]:
    """Extract UTF-8 text from TXT files."""

    try:
        text = file_path.read_text(
            encoding="utf-8-sig"
        ).strip()

    except UnicodeDecodeError as exc:
        raise DocumentExtractionError(
            "TXT file must contain valid UTF-8 text."
        ) from exc

    except OSError as exc:
        raise DocumentExtractionError(
            "Could not read TXT file."
        ) from exc

    if not text:
        raise DocumentExtractionError(
            "TXT file contains no extractable text."
        )

    return [
        ExtractedPage(
            text=text,
            page_number=None,
            source_label="TXT document",
        )
    ]