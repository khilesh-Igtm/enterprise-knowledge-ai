from unittest.mock import MagicMock

import pytest

from app.services.embeddings import GeminiEmbeddingService


@pytest.mark.asyncio
async def test_embedding_service_returns_vectors():
    service = GeminiEmbeddingService.__new__(GeminiEmbeddingService)
    service.dimensions = 3
    service.batch_size = 2

    fake_response = MagicMock()
    fake_response.embeddings = [
        MagicMock(values=[0.1, 0.2, 0.3]),
        MagicMock(values=[0.4, 0.5, 0.6]),
    ]

    service._embed_batch = MagicMock(return_value=[
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ])

    vectors = await service.embed_documents(["first", "second"])

    assert len(vectors) == 2
    assert all(len(vector) == 3 for vector in vectors)


@pytest.mark.asyncio
async def test_empty_embedding_input():
    service = GeminiEmbeddingService.__new__(GeminiEmbeddingService)

    assert await service.embed_documents([]) == []