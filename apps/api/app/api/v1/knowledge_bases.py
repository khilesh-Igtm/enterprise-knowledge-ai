from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
)

router = APIRouter(
    prefix="/knowledge-bases",
    tags=["Knowledge Bases"],
)


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
    knowledge_base_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid

    try:
        parsed_id = uuid.UUID(knowledge_base_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    knowledge_base = await db.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.id == parsed_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )

    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    return knowledge_base