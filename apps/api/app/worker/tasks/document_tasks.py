import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.integrations.qdrant import create_qdrant_client, ensure_collection
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.services.chunking import chunk_document
from app.services.embeddings import GeminiEmbeddingService
from app.services.extraction import extract_document
from app.services.storage import resolve_storage_path
from app.services.vector_store import store_chunks
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


async def process_document_async(document_id: UUID) -> dict:
    engine = create_async_engine(settings.DATABASE_URL)

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    qdrant = create_qdrant_client()

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(Document, KnowledgeBase.user_id)
                .join(
                    KnowledgeBase,
                    Document.knowledge_base_id == KnowledgeBase.id,
                )
                .where(Document.id == document_id)
            )

            row = result.one_or_none()

            if row is None:
                return {"status": "not_found"}

            document, user_id = row

            if document.status == "processed":
                return {"status": "already_processed"}

            document.status = "processing"
            await session.commit()

            document_id = document.id
            knowledge_base_id = document.knowledge_base_id
            filename = document.filename
            storage_key = document.storage_path

        file_path = resolve_storage_path(storage_key)

        if not file_path.is_file():
            raise FileNotFoundError("Stored document file does not exist.")

        pages = await asyncio.to_thread(
            extract_document,
            file_path,
        )

        chunks = chunk_document(
            pages=pages,
            document_id=document_id,
            knowledge_base_id=knowledge_base_id,
            user_id=user_id,
        )

        if not chunks:
            raise ValueError("Document produced no chunks.")

        embedding_service = GeminiEmbeddingService()

        vectors = await embedding_service.embed_documents(
            [chunk.text for chunk in chunks]
        )

        await ensure_collection(qdrant)

        await store_chunks(
            client=qdrant,
            chunks=chunks,
            vectors=vectors,
            filename=filename,
        )

        async with session_factory() as session:
            document = await session.get(Document, document_id)

            if document is None:
                raise ValueError("Document was deleted during processing.")

            document.status = "processed"
            await session.commit()

        logger.info(
            "Document processing completed: %s (%s chunks)",
            document_id,
            len(chunks),
        )

        return {
            "status": "processed",
            "document_id": str(document_id),
            "chunks_created": len(chunks),
        }

    except Exception:
        logger.exception("Document processing failed: %s", document_id)

        try:
            async with session_factory() as session:
                document = await session.get(Document, document_id)

                if document is not None:
                    document.status = "failed"
                    await session.commit()
        except SQLAlchemyError:
            logger.exception("Could not update document failure status.")

        raise

    finally:
        await qdrant.close()
        await engine.dispose()





@celery_app.task(
    bind=True,
    name="documents.process_document",
    max_retries=3,
    default_retry_delay=30,
)
def process_document(self, document_id: str) -> dict:
    try:
        return asyncio.run(
            process_document_async(UUID(document_id))
        )
    except Exception as exc:
        logger.exception("Celery document task failed.")
        raise self.retry(exc=exc) from exc