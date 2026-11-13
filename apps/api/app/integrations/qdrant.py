from qdrant_client import AsyncQdrantClient, models

from app.core.config import settings


def create_qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        timeout=30,
    )


async def ensure_collection(
    client: AsyncQdrantClient,
) -> None:
    collection_name = settings.QDRANT_COLLECTION_NAME

    exists = await client.collection_exists(collection_name)

    if not exists:
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=settings.GEMINI_EMBEDDING_DIMENSIONS,
                distance=models.Distance.COSINE,
            ),
        )

    indexes = {
        "user_id": models.PayloadSchemaType.KEYWORD,
        "knowledge_base_id": models.PayloadSchemaType.KEYWORD,
        "document_id": models.PayloadSchemaType.KEYWORD,
    }

    for field_name, field_schema in indexes.items():
        await client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=field_schema,
        )