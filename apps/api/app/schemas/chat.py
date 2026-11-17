import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    knowledge_base_id: uuid.UUID
    title: str | None = Field(
        default=None,
        max_length=200,
    )


class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    knowledge_base_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=12000,
    )


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    citations: list[dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse]


class ChatResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
