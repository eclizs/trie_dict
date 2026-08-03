

from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from ..database import get_db
from ..models import Entry, User

router = APIRouter()

@router.get("/dict", status_code=status.HTTP_200_OK)
async def get_dict(session: Annotated[AsyncSession, Depends(get_db)], user: User):
    result = await session.execute(select(Entry.entry).where(Entry.user_id == user.id))
    return result.scalars().all()
