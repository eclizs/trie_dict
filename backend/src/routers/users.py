from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from uuid import uuid4, UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import hash_password, verify_password
from ..database import get_db
from ..models import User
from ..schema import UserCreate, UserLogin, UserRead

router = APIRouter()


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    result = await session.execute(
        select(User).where(func.lower(User.email) == email.lower())
    )
    return result.scalars().first()

async def get_identity(request: Request) -> str:
    identity = request.session.get("identity")

    if identity is None:
        identity = f"guest:{uuid4()}"
        request.session["identity"] = identity

    return identity

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

Identity = Annotated[str, Depends(get_identity)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]

async def get_current_user(
    identity: Identity,
    session: DatabaseSession
) -> User:
    if not identity.startswith("user:"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    user_id = int(identity.removeprefix("user:"))
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists"
        )

    return user

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserCreate,
    session: DatabaseSession
) -> User:
    existing_user = await get_user_by_email(session, user_data.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    user = User(
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password),
        created_at=datetime.now(UTC)
    )

    session.add(user)

    try:
        await session.commit()
        await session.refresh(user)
    except:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    request.session.clear()
    request.session["identity"] = f"user:{user.id}"

    return user

@router.post("/login", response_model=UserRead)
async def login(
    request: Request,
    credentials: UserLogin,
    session: DatabaseSession
) -> User:
    user = await get_user_by_email(session, credentials.email)

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    request.session.clear()
    request.session["identity"] = f"user:{user.id}"

    return user

@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request) -> Response:
    identity = request.session.get("identity")

    request.session.clear()

    return Response(status_code=status.HTTP_204_NO_CONTENT)