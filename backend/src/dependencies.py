from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .crud import get_user_by_id
from .database import get_db
from .models import User


DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


def identity_is_valid(identity: object) -> bool:
    if not isinstance(identity, str):
        return False

    if identity.startswith("user:"):
        try:
            return int(identity.removeprefix("user:")) > 0
        except ValueError:
            return False

    if identity.startswith("guest:"):
        try:
            UUID(identity.removeprefix("guest:"))
            return True
        except ValueError:
            return False

    return False


def get_user_id(identity: str) -> int:
    if identity.startswith("user:"):
        return int(identity.removeprefix("user:"))
    if identity.startswith("guest:"):
        return -1
    raise ValueError("Invalid identity")


async def get_identity(
    request: Request,
    session: DatabaseSession,
) -> str:
    identity = request.session.get("identity")

    if identity_is_valid(identity):
        if identity.startswith("guest:"):
            return identity

        user = await get_user_by_id(session, get_user_id(identity))
        if user is not None:
            return identity

    request.session.clear()
    identity = f"guest:{uuid4()}"
    request.session["identity"] = identity

    return identity


Identity = Annotated[str, Depends(get_identity)]


async def get_current_user(
    identity: Identity,
    session: DatabaseSession,
) -> User:
    if not identity.startswith("user:"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user = await get_user_by_id(session, get_user_id(identity))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    return user
