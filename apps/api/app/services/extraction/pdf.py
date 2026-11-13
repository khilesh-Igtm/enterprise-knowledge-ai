from pathlib import Path

import fitz

from app.services.extraction.types import (
    DocumentExtractionError,
    ExtractedPage,
)


def extract_pdf(file_path: Path) -> list[ExtractedPage]:
    """
    Extract text from PDF page by page.

    Page numbers are 1-based.
    Scanned/image-only PDFs are not supported yet.
    """

    extracted_pages: list[ExtractedPage] = []

    try:
        with fitz.open(file_path) as pdf:

            if pdf.is_encrypted:
                raise DocumentExtractionError(
                    "Password-protected PDFs are not supported."
                )

            for page_index, page in enumerate(pdf):

                text = page.get_text(
                    "text",
                    sort=True,
                ).strip()

                if not text:
                    continue

                extracted_pages.append(
                    ExtractedPage(
                        text=text,
                        page_number=page_index + 1,
                        source_label=f"Page {page_index + 1}",
                    )
                )

    except DocumentExtractionError:
        raise

    except (fitz.FileDataError, RuntimeError, OSError) as exc:
        raise DocumentExtractionError(
            "Could not extract text from PDF."
        ) from exc

    if not extracted_pages:
        raise DocumentExtractionError(
            "PDF contains no extractable text. "
            "Scanned PDFs may require OCR."
        )

    return extracted_pages