from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.services.tag_service import (
    create_tag, delete_tag, get_owned_tag, list_tags, update_tag,
)
from app.services.todo_service import invalidate_user_cache

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def get_tags(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await list_tags(db, current_user.id)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    try:
        tag = await create_tag(db, data, current_user.id)
        await invalidate_user_cache(redis, current_user.id)
        return tag
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Tag name already exists") from exc


@router.patch("/{tag_id}", response_model=TagResponse)
async def rename_tag(tag_id: UUID, data: TagUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    tag = await get_owned_tag(db, tag_id, current_user.id)
    if tag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tag not found")
    try:
        updated = await update_tag(db, tag, data)
        await invalidate_user_cache(redis, current_user.id)
        return updated
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Tag name already exists") from exc


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag(tag_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    tag = await get_owned_tag(db, tag_id, current_user.id)
    if tag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tag not found")
    await delete_tag(db, tag)
    await invalidate_user_cache(redis, current_user.id)