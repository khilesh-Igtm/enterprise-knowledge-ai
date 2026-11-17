from dataclasses import dataclass
from typing import Any
from uuid import UUID

import tiktoken
from qdrant_client import AsyncQdrantClient, models

from app.core.config import settings
from app.services.embeddings import GeminiEmbeddingService


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    text: str
    score: float
    page_number: int | None
    source_label: str | None
    chunk_index: int


async def retrieve_chunks(
    client: AsyncQdrantClient,
    embedding_service: GeminiEmbeddingService,
    query: str,
    user_id: UUID,
    knowledge_base_id: UUID,
) -> list[RetrievedChunk]:

    query_vector = await embedding_service.embed_query(query)

    query_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="user_id",
                match=models.MatchValue(
                    value=str(user_id),
                ),
            ),
            models.FieldCondition(
                key="knowledge_base_id",
                match=models.MatchValue(
                    value=str(knowledge_base_id),
                ),
            ),
        ]
    )

    response = await client.query_points(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=settings.CHAT_TOP_K,
        with_payload=True,
        with_vectors=False,
    )

    chunks: list[RetrievedChunk] = []

    for point in response.points:
        payload: dict[str, Any] = point.payload or {}

        score = float(point.score or 0.0)

        if score < settings.CHAT_SCORE_THRESHOLD:
            continue

        text = payload.get("text")

        if not isinstance(text, str) or not text.strip():
            continue

        chunks.append(
            RetrievedChunk(
                chunk_id=str(point.id),
                document_id=str(payload.get("document_id", "")),
                filename=str(payload.get("filename", "Unknown")),
                text=text,
                score=score,
                page_number=payload.get("page_number"),
                source_label=payload.get("source_label"),
                chunk_index=int(payload.get("chunk_index", 0)),
            )
        )

    return chunks


def build_context(
    chunks: list[RetrievedChunk],
) -> tuple[str, list[dict[str, Any]]]:

    encoding = tiktoken.get_encoding("cl100k_base")

    remaining_tokens = settings.CHAT_MAX_CONTEXT_TOKENS

    context_parts: list[str] = []
    citations: list[dict[str, Any]] = []

    for chunk in chunks:
        citation_number = len(citations) + 1

        source = (
            f"[{citation_number}] "
            f"File: {chunk.filename}\n"
            f"Page: {chunk.page_number if chunk.page_number is not None else 'N/A'}\n"
            f"Chunk: {chunk.chunk_index}\n"
            f"Content:\n{chunk.text}"
        )

        tokens = encoding.encode(source)

        if len(tokens) > remaining_tokens:
            if not context_parts:
                truncated = encoding.decode(tokens[:remaining_tokens])

                context_parts.append(truncated)

                citations.append(
                    {
                        "citation_number": citation_number,
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "filename": chunk.filename,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                        "score": chunk.score,
                        "source_label": chunk.source_label,
                    }
                )

            break

        context_parts.append(source)
        remaining_tokens -= len(tokens)

        citations.append(
            {
                "citation_number": citation_number,
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "score": chunk.score,
                "source_label": chunk.source_label,
            }
        )

    return "\n\n---\n\n".join(context_parts), citations
