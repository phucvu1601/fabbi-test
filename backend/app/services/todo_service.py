import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.redis import RedisClient
from app.models.tag import todo_tags
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
    status_filter: bool | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Todo], int]:
    """Get all todos with pagination for a specific user."""
    conditions = [Todo.user_id == user_id]
    if status_filter is not None:
        conditions.append(Todo.completed.is_(status_filter))
    if tag_id:
        conditions.append(
            select(todo_tags.c.todo_id)
            .where(todo_tags.c.todo_id == Todo.id, todo_tags.c.tag_id == tag_id)
            .exists()
        )
    if keyword:
        pattern = f"%{keyword}%"
        conditions.append(or_(Todo.title.ilike(pattern), Todo.description.ilike(pattern)))
    if date_from:
        conditions.append(
            Todo.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to:
        conditions.append(
            Todo.created_at < datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        )

    query = select(Todo).options(selectinload(Todo.tags)).where(*conditions).order_by(
        Todo.created_at.desc(), Todo.id.desc()
    ).offset(skip).limit(limit)
    result = await db.execute(query)
    todos = list(result.scalars().all())

    # Count total
    count_query = select(func.count()).select_from(Todo).where(*conditions)
    total = await db.execute(count_query)

    return todos, total.scalar_one()


async def get_todo_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:
    result = await db.execute(
        select(Todo).options(selectinload(Todo.tags)).where(Todo.id == todo_id)
    )
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


async def bulk_update_status(
    db: AsyncSession,
    user_id: uuid.UUID,
    todo_ids: list[uuid.UUID],
    completed: bool,
) -> list[Todo]:
    result = await db.execute(
        select(Todo)
        .options(selectinload(Todo.tags))
        .where(Todo.user_id == user_id, Todo.id.in_(set(todo_ids)))
    )
    todos = list(result.scalars().all())
    if len(todos) != len(set(todo_ids)):
        return []
    await db.execute(
        update(Todo)
        .where(Todo.user_id == user_id, Todo.id.in_(set(todo_ids)))
        .values(completed=completed)
    )
    await db.flush()
    return todos

async def invalidate_user_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    """Clear all cached todo list pages for a specific user."""
    pattern = f"todos:user:{user_id}:*"

    # Scan and collect all matching keys
    keys_to_delete = [key async for key in redis.scan_iter(match=pattern)]

    # Delete collected keys in a single batch
    if keys_to_delete:
        await redis.delete_many(keys_to_delete)
