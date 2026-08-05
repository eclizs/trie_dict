from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Entry, User


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    result = await session.execute(
        select(User).where(func.lower(User.email) == email.lower())
    )
    return result.scalars().first()


async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def create_user_with_entries(
    session: AsyncSession,
    user: User,
    entries: Iterable[str] = (),
) -> User:
    session.add(user)
    await session.flush()

    session.add_all(
        Entry(user_id=user.id, entry=entry)
        for entry in entries
    )

    await session.commit()
    return user
