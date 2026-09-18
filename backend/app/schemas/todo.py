import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.tag import TodoTagResponse


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class TodoUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    completed: bool | None = None


class TodoResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    completed: bool
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    user_email: str | None = None
    tags: list[TodoTagResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TodoListResponse(BaseModel):
    items: list[TodoResponse]
    total: int
    page: int
    page_size: int


class BulkTodoStatusUpdate(BaseModel):
    todo_ids: list[uuid.UUID] = Field(..., min_length=1)
    completed: bool
