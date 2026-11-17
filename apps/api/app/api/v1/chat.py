import logging
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from qdrant_client import AsyncQdrantClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.knowledge_base import KnowledgeBase
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import (
    ChatResponse,
    ConversationCreate,
    ConversationDetail,
    ConversationResponse,
    MessageCreate,
)
from app.services.chat import RAGChatService
from app.services.embeddings import GeminiEmbeddingService
from app.services.retrieval import retrieve_chunks

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


async def get_owned_conversation(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Conversation:

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )

    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return conversation


async def verify_knowledge_base_ownership(
    knowledge_base_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:

    result = await db.scalar(
        select(KnowledgeBase.id).where(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.user_id == user_id,
        )
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found.",
        )


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    await verify_knowledge_base_ownership(
        payload.knowledge_base_id,
        current_user.id,
        db,
    )

    conversation = Conversation(
        user_id=current_user.id,
        knowledge_base_id=payload.knowledge_base_id,
        title=payload.title or "New conversation",
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return conversation


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
async def list_conversations(
    knowledge_base_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    query = select(Conversation).where(
        Conversation.user_id == current_user.id,
    )

    if knowledge_base_id is not None:
        query = query.where(
            Conversation.knowledge_base_id == knowledge_base_id,
        )

    result = await db.scalars(query.order_by(Conversation.updated_at.desc()))

    return result.all()


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    conversation = await get_owned_conversation(
        conversation_id,
        current_user.id,
        db,
    )

    messages = await db.scalars(
        select(Message)
        .where(
            Message.conversation_id == conversation.id,
        )
        .order_by(Message.created_at.asc())
    )

    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "knowledge_base_id": conversation.knowledge_base_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": messages.all(),
    }


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatResponse,
)
async def send_message(
    conversation_id: uuid.UUID,
    payload: MessageCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    conversation = await get_owned_conversation(
        conversation_id,
        current_user.id,
        db,
    )

    qdrant: AsyncQdrantClient = request.app.state.qdrant

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.content.strip(),
        citations=[],
    )

    db.add(user_message)

    try:
        await db.commit()
        await db.refresh(user_message)

    except Exception:
        await db.rollback()
        raise

    previous_messages = await db.scalars(
        select(Message)
        .where(
            Message.conversation_id == conversation.id,
            Message.id != user_message.id,
        )
        .order_by(Message.created_at.desc())
        .limit(settings.CHAT_HISTORY_MESSAGES)
    )

    history_rows = list(reversed(previous_messages.all()))

    history = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in history_rows
    ]

    try:
        embedding_service = GeminiEmbeddingService()

        chunks = await retrieve_chunks(
            client=qdrant,
            embedding_service=embedding_service,
            query=payload.content,
            user_id=current_user.id,
            knowledge_base_id=conversation.knowledge_base_id,
        )

        chat_service = RAGChatService()

        try:
            answer, citations = await chat_service.generate_answer(
                question=payload.content,
                chunks=chunks,
                history=history,
            )
        finally:
            await chat_service.close()

    except Exception as exc:
        logger.exception(
            "RAG chat generation failed for conversation %s",
            conversation.id,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate an answer. Please try again.",
        ) from exc

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        citations=citations,
    )

    if conversation.title == "New conversation":
        conversation.title = payload.content.strip()[:200]

    db.add(assistant_message)

    try:
        await db.commit()
        await db.refresh(assistant_message)
        await db.refresh(conversation)

    except Exception:
        await db.rollback()
        raise

    return {
        "user_message": user_message,
        "assistant_message": assistant_message,
    }


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    conversation = await get_owned_conversation(
        conversation_id,
        current_user.id,
        db,
    )

    await db.delete(conversation)
    await db.commit()
