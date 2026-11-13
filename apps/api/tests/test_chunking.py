from uuid import uuid4

from app.services.chunking import chunk_document
from app.services.extraction.types import ExtractedPage


def test_chunk_document_preserves_page_numbers():
    document_id = uuid4()
    knowledge_base_id = uuid4()
    user_id = uuid4()

    pages = [
        ExtractedPage(
            text="This is page one. " * 100,
            page_number=1,
            source_label="Page 1",
        ),
        ExtractedPage(
            text="This is page two. " * 100,
            page_number=2,
            source_label="Page 2",
        ),
    ]

    chunks = chunk_document(
        pages,
        document_id,
        knowledge_base_id,
        user_id,
    )

    assert chunks
    assert all(chunk.document_id == document_id for chunk in chunks)
    assert all(chunk.knowledge_base_id == knowledge_base_id for chunk in chunks)
    assert all(chunk.user_id == user_id for chunk in chunks)

    assert {chunk.page_number for chunk in chunks} == {1, 2}


def test_chunk_ids_are_deterministic():
    document_id = uuid4()
    knowledge_base_id = uuid4()
    user_id = uuid4()

    pages = [
        ExtractedPage(
            text="Example content. " * 100,
            page_number=1,
        )
    ]

    first = chunk_document(pages, document_id, knowledge_base_id, user_id)
    second = chunk_document(pages, document_id, knowledge_base_id, user_id)

    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]


def test_empty_document_returns_no_chunks():
    chunks = chunk_document(
        [],
        uuid4(),
        uuid4(),
        uuid4(),
    )

    assert chunks == []