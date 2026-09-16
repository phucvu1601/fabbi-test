import json

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis, get_valid_todo
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.todo import Todo
from app.models.user import User
from app.schemas.todo import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate
from app.services.todo_service import (
    create_todo,
    delete_todo,
    get_todos,
    invalidate_user_cache,
    update_todo,
)

router = APIRouter()

CACHE_TTL = 300  # 5 minutes


@router.get("", response_model=TodoListResponse)
async def list_todos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get paginated list of todos."""
    skip = (page - 1) * size

    # FIX 1: Dynamic Cache Key including user_id, page and size
    cache_key = f"todos:user:{current_user.id}:page:{page}:size:{size}"

    # Try to get from cache
    cached = await redis.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        return TodoListResponse(**cached_data)

    todos, total = await get_todos(db, user_id=current_user.id, skip=skip, limit=size)

    # FIX 2: Prevent N+1 query by using current_user context directly
    items = [
        TodoResponse(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            completed=todo.completed,
            user_id=todo.user_id,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
            user_email=current_user.email,  # Reused from auth context
        )
        for todo in todos
    ]

    response = TodoListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )

    # Cache the response
    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL)

    return response


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
    
    return todo


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo: Todo = Depends(get_valid_todo),
):
    """Get a specific todo by ID."""
    return todo


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

    return updated_todo


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
