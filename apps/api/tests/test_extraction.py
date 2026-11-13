import fitz
import pytest
from docx import Document

from app.services.extraction import (
    DocumentExtractionError,
    extract_document,
)


def test_extract_txt(tmp_path):
    file_path = tmp_path / "sample.txt"

    file_path.write_text(
        "Enterprise Knowledge AI\n"
        "Document extraction testing.",
        encoding="utf-8",
    )

    pages = extract_document(file_path)

    assert len(pages) == 1
    assert pages[0].page_number is None
    assert "Enterprise Knowledge AI" in pages[0].text


def test_extract_pdf(tmp_path):
    file_path = tmp_path / "sample.pdf"

    pdf = fitz.open()

    page = pdf.new_page()
    page.insert_text(
        (72, 72),
        "Enterprise Knowledge AI PDF testing.",
    )

    pdf.save(file_path)
    pdf.close()

    pages = extract_document(file_path)

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Enterprise Knowledge AI" in pages[0].text


def test_extract_docx(tmp_path):
    file_path = tmp_path / "sample.docx"

    document = Document()

    document.add_paragraph(
        "Enterprise Knowledge AI DOCX testing."
    )

    table = document.add_table(
        rows=1,
        cols=2,
    )

    table.cell(0, 0).text = "Name"
    table.cell(0, 1).text = "Value"

    document.save(file_path)

    pages = extract_document(file_path)

    assert len(pages) == 1
    assert "Enterprise Knowledge AI" in pages[0].text
    assert "Name | Value" in pages[0].text


def test_reject_empty_txt(tmp_path):
    file_path = tmp_path / "empty.txt"
    file_path.write_text("", encoding="utf-8")

    with pytest.raises(DocumentExtractionError):
        extract_document(file_path)


def test_reject_unsupported_file(tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text("name,value")

    with pytest.raises(DocumentExtractionError):
        extract_document(file_path)


def test_reject_missing_file(tmp_path):
    file_path = tmp_path / "missing.pdf"

    with pytest.raises(DocumentExtractionError):
        extract_document(file_path)


def test_reject_empty_pdf(tmp_path):
    file_path = tmp_path / "empty.pdf"

    pdf = fitz.open()
    pdf.new_page()
    pdf.save(file_path)
    pdf.close()

    with pytest.raises(DocumentExtractionError):
        extract_document(file_path)