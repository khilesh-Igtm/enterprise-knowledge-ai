import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.services.storage import delete_file

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/knowledge-bases",
    tags=["Knowledge Bases"],
)


async def get_owned_knowledge_base(
    knowledge_base_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    include_documents: bool = False,
) -> KnowledgeBase:
    query = select(KnowledgeBase).where(
        KnowledgeBase.id == knowledge_base_id,
        KnowledgeBase.user_id == user_id,
    )

    if include_documents:
        query = query.options(selectinload(KnowledgeBase.documents))

    knowledge_base = await db.scalar(query)

    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    return knowledge_base


@router.post(
    "",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    knowledge_base = KnowledgeBase(
        name=payload.name,
        description=payload.description,
        user_id=current_user.id,
    )

    db.add(knowledge_base)
    await db.commit()
    await db.refresh(knowledge_base)

    return knowledge_base


@router.get(
    "",
    response_model=list[KnowledgeBaseResponse],
)
async def list_knowledge_bases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.scalars(
        select(KnowledgeBase)
        .where(KnowledgeBase.user_id == current_user.id)
        .order_by(KnowledgeBase.created_at.desc())
    )

    return result.all()


@router.get(
    "/{knowledge_base_id}",
    response_model=KnowledgeBaseResponse,
)
async def get_knowledge_base(
    knowledge_base_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_owned_knowledge_base(
        knowledge_base_id,
        current_user.id,
        db,
    )


@router.patch(
    "/{knowledge_base_id}",
    response_model=KnowledgeBaseResponse,
)
async def update_knowledge_base(
    knowledge_base_id: uuid.UUID,
    payload: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    knowledge_base = await get_owned_knowledge_base(
        knowledge_base_id,
        current_user.id,
        db,
    )

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(knowledge_base, field, value)

    await db.commit()
    await db.refresh(knowledge_base)

    return knowledge_base


@router.delete(
    "/{knowledge_base_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_knowledge_base(
    knowledge_base_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    knowledge_base = await get_owned_knowledge_base(
        knowledge_base_id,
        current_user.id,
        db,
        include_documents=True,
    )

    storage_keys = [document.storage_path for document in knowledge_base.documents]

    await db.delete(knowledge_base)
    await db.commit()

    for storage_key in storage_keys:
        try:
            delete_file(storage_key)
        except (ValueError, OSError):
            logger.exception(
                "Orphaned document file after knowledge base deletion: %s",
                storage_key,
            )
