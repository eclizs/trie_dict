from datetime import UTC, datetime
from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import User, Entry

from ..database import get_db
from ..schema import UserCreate
from ..auth import hash_password, verify_password

router = APIRouter()

async def create_user(session: Annotated[AsyncSession, Depends(get_db)], user: UserCreate) -> User:
    if await get_user_by_email(session, user.email):
        raise ValueError("User with this email already exists")
    new_user = User(
        email=user.email.lower(),
        password_hash=hash_password(user.password),
        created_at=datetime.now(UTC)
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

async def get_user_by_email(session: Annotated[AsyncSession, Depends(get_db)], email: str) -> User | None:
    result = await session.execute(select(User).where(func.lower(User.email) == email.lower()))
    return result.scalars().first()

async def authenticate_user(session: Annotated[AsyncSession, Depends(get_db)], email: str, password: str) -> bool:
    user = await get_user_by_email(session, email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return True

