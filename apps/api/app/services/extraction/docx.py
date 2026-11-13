from pathlib import Path
from zipfile import BadZipFile

from docx import Document
from docx.document import Document as DocumentObject
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.services.extraction.types import (
    DocumentExtractionError,
    ExtractedPage,
)


def extract_docx(file_path: Path) -> list[ExtractedPage]:
    """
    Extract paragraphs and tables from DOCX.

    Preserves paragraph/table ordering where possible.
    DOCX pagination is not reliable through python-docx.
    """

    try:
        document: DocumentObject = Document(file_path)

        content_blocks: list[str] = []

        for block in document.iter_inner_content():

            if isinstance(block, Paragraph):
                text = block.text.strip()

                if text:
                    content_blocks.append(text)

            elif isinstance(block, Table):

                for row in block.rows:
                    cells = [
                        cell.text.strip()
                        for cell in row.cells
                    ]

                    row_text = " | ".join(
                        cell for cell in cells if cell
                    )

                    if row_text:
                        content_blocks.append(row_text)

    except (BadZipFile, PackageNotFoundError, ValueError, OSError) as exc:
        raise DocumentExtractionError(
            "Could not extract text from DOCX."
        ) from exc

    text = "\n\n".join(content_blocks).strip()

    if not text:
        raise DocumentExtractionError(
            "DOCX contains no extractable text."
        )

    return [
        ExtractedPage(
            text=text,
            page_number=None,
            source_label="DOCX document",
        )
    ]