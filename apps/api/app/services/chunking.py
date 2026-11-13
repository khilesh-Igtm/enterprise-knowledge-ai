from dataclasses import dataclass
from uuid import NAMESPACE_URL, UUID, uuid5

import tiktoken

from app.core.config import settings
from app.services.extraction.types import ExtractedPage


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    id: UUID
    document_id: UUID
    knowledge_base_id: UUID
    user_id: UUID
    chunk_index: int
    text: str
    page_number: int | None
    source_label: str | None


def chunk_document(
    pages: list[ExtractedPage],
    document_id: UUID,
    knowledge_base_id: UUID,
    user_id: UUID,
) -> list[DocumentChunk]:
    chunk_size = settings.CHUNK_SIZE
    overlap = settings.CHUNK_OVERLAP

    if chunk_size <= 0:
        raise ValueError("CHUNK_SIZE must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")

    encoding = tiktoken.get_encoding("cl100k_base")
    chunks: list[DocumentChunk] = []
    chunk_index = 0
    step = chunk_size - overlap

    for page in pages:
        tokens = encoding.encode(page.text)

        for start in range(0, len(tokens), step):
            token_slice = tokens[start : start + chunk_size]

            if not token_slice:
                continue

            text = encoding.decode(token_slice).strip()

            if not text:
                continue

            chunk_id = uuid5(
                NAMESPACE_URL,
                f"{document_id}:{chunk_index}",
            )

            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    document_id=document_id,
                    knowledge_base_id=knowledge_base_id,
                    user_id=user_id,
                    chunk_index=chunk_index,
                    text=text,
                    page_number=page.page_number,
                    source_label=page.source_label,
                )
            )

            chunk_index += 1

    return chunks