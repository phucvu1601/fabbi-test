import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import RedisClient
from app.models.todo import Todo
from app.schemas.todo import TodoCreate


async def create_todo(
    db: AsyncSession, todo_data: TodoCreate, user_id: uuid.UUID
) -> Todo:
    todo = Todo(
        title=todo_data.title,
        description=todo_data.description,
        user_id=user_id,
    )
    db.add(todo)
    await db.flush()
    await db.refresh(todo)
    return todo


async def get_todos(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Todo], int]:
    """Get all todos with pagination for a specific user."""
    # Ensure consistent pagination ordering (newest first)
    query = (
        select(Todo)
        .where(Todo.user_id == user_id)
        .order_by(Todo.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    todos = list(result.scalars().all())

    # Count total
    count_query = select(func.count()).select_from(Todo).where(Todo.user_id == user_id)
    total = await db.execute(count_query)

    return todos, total.scalar_one()


async def get_todo_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:
    result = await db.execute(select(Todo).where(Todo.id == todo_id))
    return result.scalar_one_or_none()


async def update_todo(db: AsyncSession, todo: Todo, update_data: dict) -> Todo:
    for key, value in update_data.items():
        setattr(todo, key, value)
    await db.flush()
    await db.refresh(todo)
    return todo


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    await db.delete(todo)
    await db.flush()

async def invalidate_user_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    """Clear all cached todo list pages for a specific user."""
    pattern = f"todos:user:{user_id}:*"

    # Scan and collect all matching keys
    keys_to_delete = [key async for key in redis.scan_iter(match=pattern)]

    # Delete collected keys in a single batch
    if keys_to_delete:
        await redis.delete_many(keys_to_delete)
