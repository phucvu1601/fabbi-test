import json
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user, get_redis, get_valid_todo
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.todo import Todo
from app.models.user import User
from app.schemas.tag import TagResponse, TodoTagCreate
from app.schemas.todo import (
    BulkTodoStatusUpdate,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoUpdate,
)
from app.services.todo_service import (
    create_todo,
    delete_todo,
    get_todos,
    bulk_update_status,
    invalidate_user_cache,
    update_todo,
)
from app.services.tag_service import attach_tag, detach_tag, get_owned_tag

router = APIRouter()

CACHE_TTL = 300  # 5 minutes


def todo_response(todo: Todo, user_email: str, tags=None) -> TodoResponse:
    return TodoResponse(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        user_id=todo.user_id,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        user_email=user_email,
        tags=tags if tags is not None else [],
    )


@router.get("", response_model=TodoListResponse)
async def list_todos(
    status_filter: bool | None = Query(None, alias="status"),
    tag_id: UUID | None = None,
    keyword: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get paginated list of todos."""
    skip = (page - 1) * page_size

    cache_key = (
        f"todos:user:{current_user.id}:page:{page}:size:{page_size}:"
        f"status:{status_filter if status_filter is not None else '-'}:"
        f"tag:{tag_id or '-'}:keyword:{keyword or '-'}:"
        f"from:{date_from or '-'}:to:{date_to or '-'}"
    )

    # Try to get from cache
    cached = await redis.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        return TodoListResponse(**cached_data)

    todos, total = await get_todos(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
        status_filter=status_filter,
        tag_id=tag_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )

    # FIX 2: Prevent N+1 query by using current_user context directly
    items = [todo_response(todo, current_user.email, todo.tags) for todo in todos]

    response = TodoListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )

    # Cache the response
    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)

    return response


@router.patch("/bulk-status", response_model=list[TodoResponse])
async def update_todos_status(
    data: BulkTodoStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    todos = await bulk_update_status(db, current_user.id, data.todo_ids, data.completed)
    if not todos:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "All todo IDs must belong to the current user",
        )
    await invalidate_user_cache(redis, current_user.id)
    return [todo_response(todo, current_user.email, todo.tags) for todo in todos]


@router.post("/{todo_id}/tags", response_model=TagResponse)
async def add_tag_to_todo(
    data: TodoTagCreate,
    todo: Todo = Depends(get_valid_todo),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    tag = await get_owned_tag(db, data.tag_id, current_user.id)
    if tag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tag not found")
    try:
        await attach_tag(db, tag, todo.id)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Tag is already attached") from exc
    await invalidate_user_cache(redis, current_user.id)
    return tag


@router.delete("/{todo_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_todo(
    tag_id: UUID,
    todo: Todo = Depends(get_valid_todo),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    tag = await get_owned_tag(db, tag_id, current_user.id)
    if tag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tag not found")
    await detach_tag(db, tag.id, todo.id)
    await invalidate_user_cache(redis, current_user.id)


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_new_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Create a new todo item."""
    todo = await create_todo(db, todo_data, current_user.id)
    
    # FIX 3: Invalidate user's list cache after creating a todo
    await invalidate_user_cache(redis, current_user.id)
    
    return todo_response(todo, current_user.email)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo: Todo = Depends(get_valid_todo),
    current_user: User = Depends(get_current_user),
):
    """Get a specific todo by ID."""
    return todo_response(todo, current_user.email, todo.tags)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_existing_todo(
    todo_data: TodoUpdate,
    todo: Todo = Depends(get_valid_todo),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Update a todo item."""
    # Extract only explicitly sent fields
    update_data = todo_data.model_dump(exclude_unset=True)

    # Apply updates via service
    updated_todo = await update_todo(db, todo, update_data)

    # FIX 3: Invalidate user's list cache after updating a todo
    await invalidate_user_cache(redis, current_user.id)

    return todo_response(updated_todo, current_user.email, updated_todo.tags)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_todo(
    todo: Todo = Depends(get_valid_todo),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete a todo item."""
    await delete_todo(db, todo)

    # FIX 3: Invalidate user's list cache after deleting a todo
    await invalidate_user_cache(redis, current_user.id)

    return None
