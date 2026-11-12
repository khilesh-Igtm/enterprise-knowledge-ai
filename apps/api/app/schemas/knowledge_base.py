import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None

    @model_validator(mode="after")
    def validate_name(self):
        self.name = self.name.strip()

        if not self.name:
            raise ValueError("Knowledge base name cannot be empty")

        return self


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    description: str | None = None

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("Knowledge base name cannot be null")

        if self.name is not None:
            self.name = self.name.strip()

            if not self.name:
                raise ValueError("Knowledge base name cannot be empty")

        return self


class KnowledgeBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
