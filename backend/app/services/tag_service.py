import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag, todo_tags
from app.schemas.tag import TagCreate, TagUpdate


async def list_tags(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    result = await db.execute(
        select(Tag).where(Tag.user_id == user_id).order_by(Tag.name.asc(), Tag.id.asc())
    )
    return list(result.scalars().all())


async def get_owned_tag(db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID) -> Tag | None:
    result = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id))
    return result.scalar_one_or_none()


async def create_tag(db: AsyncSession, data: TagCreate, user_id: uuid.UUID) -> Tag:
    tag = Tag(user_id=user_id, name=data.name.strip(), color=data.color)
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


async def update_tag(db: AsyncSession, tag: Tag, data: TagUpdate) -> Tag:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tag, key, value.strip() if key == "name" and value else value)
    await db.flush()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    await db.execute(delete(todo_tags).where(todo_tags.c.tag_id == tag.id))
    await db.delete(tag)
    await db.flush()


async def attach_tag(db: AsyncSession, tag: Tag, todo_id: uuid.UUID) -> None:
    await db.execute(todo_tags.insert().values(todo_id=todo_id, tag_id=tag.id))
    await db.flush()


async def detach_tag(db: AsyncSession, tag_id: uuid.UUID, todo_id: uuid.UUID) -> None:
    await db.execute(
        delete(todo_tags).where(todo_tags.c.tag_id == tag_id, todo_tags.c.todo_id == todo_id)
    )
    await db.flush()