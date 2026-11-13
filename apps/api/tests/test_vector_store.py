from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.chunking import DocumentChunk
from app.services.vector_store import (
    VectorStoreError,
    delete_document_vectors,
    store_chunks,
)


@pytest.fixture
def sample_chunk():
    return DocumentChunk(
        id=uuid4(),
        document_id=uuid4(),
        knowledge_base_id=uuid4(),
        user_id=uuid4(),
        chunk_index=0,
        text="Enterprise knowledge management example.",
        page_number=1,
        source_label="Page 1",
    )


@pytest.mark.asyncio
async def test_store_chunks_success(sample_chunk):
    client = MagicMock()
    client.upsert = AsyncMock()

    with patch(
        "app.services.vector_store.settings.GEMINI_EMBEDDING_DIMENSIONS",
        3,
    ), patch(
        "app.services.vector_store.settings.QDRANT_COLLECTION_NAME",
        "test_collection",
    ):
        await store_chunks(
            client=client,
            chunks=[sample_chunk],
            vectors=[[0.1, 0.2, 0.3]],
            filename="example.pdf",
        )

    client.upsert.assert_awaited_once()

    call_kwargs = client.upsert.await_args.kwargs

    assert call_kwargs["collection_name"] == "test_collection"
    assert len(call_kwargs["points"]) == 1

    point = call_kwargs["points"][0]

    assert point.id == str(sample_chunk.id)
    assert point.vector == [0.1, 0.2, 0.3]
    assert point.payload["user_id"] == str(sample_chunk.user_id)
    assert point.payload["knowledge_base_id"] == str(
        sample_chunk.knowledge_base_id
    )
    assert point.payload["document_id"] == str(sample_chunk.document_id)
    assert point.payload["page_number"] == 1
    assert point.payload["filename"] == "example.pdf"


@pytest.mark.asyncio
async def test_store_chunks_empty_input():
    client = MagicMock()
    client.upsert = AsyncMock()

    await store_chunks(
        client=client,
        chunks=[],
        vectors=[],
        filename="empty.txt",
    )

    client.upsert.assert_not_awaited()


@pytest.mark.asyncio
async def test_store_chunks_rejects_mismatched_counts(sample_chunk):
    client = MagicMock()
    client.upsert = AsyncMock()

    with pytest.raises(VectorStoreError, match="counts do not match"):
        await store_chunks(
            client=client,
            chunks=[sample_chunk],
            vectors=[],
            filename="example.pdf",
        )

    client.upsert.assert_not_awaited()


@pytest.mark.asyncio
async def test_store_chunks_rejects_invalid_dimensions(sample_chunk):
    client = MagicMock()
    client.upsert = AsyncMock()

    with patch(
        "app.services.vector_store.settings.GEMINI_EMBEDDING_DIMENSIONS",
        3,
    ):
        with pytest.raises(VectorStoreError, match="dimensions"):
            await store_chunks(
                client=client,
                chunks=[sample_chunk],
                vectors=[[0.1, 0.2]],
                filename="example.pdf",
            )

    client.upsert.assert_not_awaited()


@pytest.mark.asyncio
async def test_store_chunks_wraps_qdrant_errors(sample_chunk):
    client = MagicMock()
    client.upsert = AsyncMock(side_effect=RuntimeError("Qdrant unavailable"))

    with patch(
        "app.services.vector_store.settings.GEMINI_EMBEDDING_DIMENSIONS",
        3,
    ):
        with pytest.raises(VectorStoreError, match="Failed to store vectors"):
            await store_chunks(
                client=client,
                chunks=[sample_chunk],
                vectors=[[0.1, 0.2, 0.3]],
                filename="example.pdf",
            )


@pytest.mark.asyncio
async def test_delete_document_vectors_uses_all_tenant_filters():
    client = MagicMock()
    client.delete = AsyncMock()

    user_id = str(uuid4())
    knowledge_base_id = str(uuid4())
    document_id = str(uuid4())

    with patch(
        "app.services.vector_store.settings.QDRANT_COLLECTION_NAME",
        "test_collection",
    ):
        await delete_document_vectors(
            client=client,
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
        )

    client.delete.assert_awaited_once()

    call_kwargs = client.delete.await_args.kwargs
    assert call_kwargs["collection_name"] == "test_collection"
    assert call_kwargs["wait"] is True

    conditions = call_kwargs["points_selector"].filter.must

    filters = {
        condition.key: condition.match.value
        for condition in conditions
    }

    assert filters == {
        "user_id": user_id,
        "knowledge_base_id": knowledge_base_id,
        "document_id": document_id,
    }


@pytest.mark.asyncio
async def test_delete_document_vectors_propagates_qdrant_error():
    client = MagicMock()
    client.delete = AsyncMock(side_effect=RuntimeError("Qdrant unavailable"))

    with pytest.raises(RuntimeError, match="Qdrant unavailable"):
        await delete_document_vectors(
            client=client,
            user_id=str(uuid4()),
            knowledge_base_id=str(uuid4()),
            document_id=str(uuid4()),
        )