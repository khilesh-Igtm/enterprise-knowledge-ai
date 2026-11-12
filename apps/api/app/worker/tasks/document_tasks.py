import asyncio
import logging
import os
from pathlib import Path
from uuid import UUID

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
from app.models.document import Document


logger = logging.getLogger(__name__)


DATABASE_URL = settings.DATABASE_URL

STORAGE_DIR = Path(
    os.getenv("STORAGE_DIR", "./storage")
).resolve()


async def process_document_async(
    document_id: UUID,
) -> dict:
    """
    Process a document asynchronously.

    Phase 3 responsibilities:
    1. Retrieve document metadata.
    2. Update processing status.
    3. Validate stored file.
    4. Update final status.
    """

    engine = create_async_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
    )

    try:
        async with session_factory() as session:

            result = await session.execute(
                select(Document).where(
                    Document.id == document_id
                )
            )

            document = result.scalar_one_or_none()

            if document is None:
                logger.warning(
                    "Document %s does not exist.",
                    document_id,
                )

                return {
                    "document_id": str(document_id),
                    "status": "not_found",
                }

            # Idempotency
            if document.status == "processed":
                return {
                    "document_id": str(document_id),
                    "status": "processed",
                    "message": "Already processed.",
                }

            if document.status == "failed":
                return {
                    "document_id": str(document_id),
                    "status": "failed",
                    "message": "Document previously failed.",
                }

            document.status = "processing"

            await session.commit()

            # Prevent directory traversal.
            file_path = (
                STORAGE_DIR / document.storage_path
            ).resolve()

            if not file_path.is_relative_to(STORAGE_DIR):
                raise ValueError(
                    "Invalid document storage path."
                )

            if not file_path.is_file():
                raise FileNotFoundError(
                    f"Document file not found: {document_id}"
                )

            if file_path.stat().st_size == 0:
                raise ValueError(
                    "Uploaded document is empty."
                )

            # Phase 3 validation complete.
            # Text extraction and vector indexing
            # will be implemented in subsequent phases.

            document.status = "processed"

            await session.commit()

            logger.info(
                "Document %s processing completed.",
                document_id,
            )

            return {
                "document_id": str(document_id),
                "status": "processed",
                "message": "Storage validation completed.",
            }

    except (FileNotFoundError, ValueError):
        logger.exception(
            "Permanent document validation failure: %s",
            document_id,
        )

        async with session_factory() as session:
            result = await session.execute(
                select(Document).where(
                    Document.id == document_id
                )
            )

            document = result.scalar_one_or_none()

            if document is not None:
                document.status = "failed"
                await session.commit()

        raise

    except SQLAlchemyError:
        logger.exception(
            "Database failure for document: %s",
            document_id,
        )
        raise

    finally:
        await engine.dispose()


@shared_task(
    bind=True,
    name="documents.process_document",
    max_retries=3,
    default_retry_delay=10,
    acks_late=True,
)
def process_document(
    self,
    document_id: str,
) -> dict:
    """
    Celery entry point.

    Database connectivity failures are retried.
    Permanent file validation failures are not.
    """

    try:
        return asyncio.run(
            process_document_async(
                UUID(document_id)
            )
        )

    except SQLAlchemyError as exc:
        logger.exception(
            "Database error processing document %s",
            document_id,
        )

        raise self.retry(
            exc=exc,
            countdown=10 * (2 ** self.request.retries),
        )