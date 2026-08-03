from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Entry

async def get_entries_for_user(session: AsyncSession, user_id: int) -> list[str]:
    """Return the persisted dictionary entries owned by one user."""
    result = await session.execute(
        select(Entry.entry).where(Entry.user_id == user_id)
    )
    return list(result.scalars().all())
