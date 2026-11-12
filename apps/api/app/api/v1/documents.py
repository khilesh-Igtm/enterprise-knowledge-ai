import logging
import uuid
from app.worker.tasks.document_tasks import process_document
from app.worker.celery_app import celery_app
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.api.v1.knowledge_bases import get_owned_knowledge_base
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.storage import delete_file, save_upload

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Documents"])


@router.post(
    "/knowledge-bases/{knowledge_base_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    knowledge_base_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_owned_knowledge_base(
        knowledge_base_id,
        current_user.id,
        db,
    )

    original_filename = (
        (file.filename or "document").replace("\\", "/").rsplit("/", 1)[-1]
    )

    storage_key, file_size, mime_type = await save_upload(
        file,
        knowledge_base_id,
    )

    document = Document(
        knowledge_base_id=knowledge_base_id,
        filename=original_filename,
        storage_path=storage_key,
        mime_type=mime_type,
        file_size=file_size,
        status="uploaded",
    )

    try:
        db.add(document)
        await db.commit()
        await db.refresh(document)

    except Exception:
        await db.rollback()

        try:
            delete_file(storage_key)
        except (ValueError, OSError):
            logger.exception(
                "Failed to clean up file after database error: %s",
                storage_key,
            )

        raise
    try:
        process_document.delay(str(document.id))
    except Exception:
        logger.exception(
            "Failed to dispatch document processing task: %s",
            document.id,
        )
        document.status = "failed"
        await db.commit()
        await db.refresh(document)

    return document


@router.get(
    "/knowledge-bases/{knowledge_base_id}/documents",
    response_model=list[DocumentResponse],
)
async def list_documents(
    knowledge_base_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_owned_knowledge_base(
        knowledge_base_id,
        current_user.id,
        db,
    )

    result = await db.scalars(
        select(Document)
        .where(Document.knowledge_base_id == knowledge_base_id)
        .order_by(Document.created_at.desc())
    )

    return result.all()


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document)
        .join(Document.knowledge_base)
        .where(
            Document.id == document_id,
            Document.knowledge_base.has(user_id=current_user.id),
        )
    )

    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document)
        .join(Document.knowledge_base)
        .where(
            Document.id == document_id,
            Document.knowledge_base.has(user_id=current_user.id),
        )
    )

    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    storage_key = document.storage_path

    await db.delete(document)
    await db.commit()

    try:
        delete_file(storage_key)
    except (ValueError, OSError):
        logger.exception(
            "Document deleted from database but file cleanup failed: %s",
            storage_key,
        )
