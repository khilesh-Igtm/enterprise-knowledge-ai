from qdrant_client import AsyncQdrantClient, models

from app.core.config import settings
from app.services.chunking import DocumentChunk


class VectorStoreError(Exception):
    """Raised when vector storage operations fail."""


async def store_chunks(
    client: AsyncQdrantClient,
    chunks: list[DocumentChunk],
    vectors: list[list[float]],
    filename: str,
) -> None:
    if len(chunks) != len(vectors):
        raise VectorStoreError("Chunk and vector counts do not match.")

    if not chunks:
        return

    points = []

    for chunk, vector in zip(chunks, vectors, strict=True):
        if len(vector) != settings.GEMINI_EMBEDDING_DIMENSIONS:
            raise VectorStoreError("Invalid vector dimensions.")

        points.append(
            models.PointStruct(
                id=str(chunk.id),
                vector=vector,
                payload={
                    "user_id": str(chunk.user_id),
                    "knowledge_base_id": str(chunk.knowledge_base_id),
                    "document_id": str(chunk.document_id),
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "page_number": chunk.page_number,
                    "source_label": chunk.source_label,
                    "filename": filename,
                },
            )
        )

    try:
        await client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=points,
            wait=True,
        )
    except Exception as exc:
        raise VectorStoreError("Failed to store vectors in Qdrant.") from exc


async def delete_document_vectors(
    client: AsyncQdrantClient,
    user_id: str,
    knowledge_base_id: str,
    document_id: str,
) -> None:
    await client.delete(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id),
                    ),
                    models.FieldCondition(
                        key="knowledge_base_id",
                        match=models.MatchValue(value=knowledge_base_id),
                    ),
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id),
                    ),
                ]
            )
        ),
        wait=True,
    )