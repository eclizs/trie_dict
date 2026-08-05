from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..auth import hash_password, verify_password
from ..crud import create_user_with_entries, get_user_by_email
from ..dependencies import DatabaseSession, Identity, get_current_user
from ..models import User
from ..schema import UserCreate, UserLogin, UserRead
from ..trie_state import discard_root, get_trie_words, locked_root

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    identity: Identity,
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

    try:
        if identity.startswith("guest:"):
            async with locked_root(request, identity, session) as guest_root:
                guest_entries = get_trie_words(request.app, guest_root)
                await create_user_with_entries(session, user, guest_entries)
                discard_root(request.app, identity)
        else:
            await create_user_with_entries(session, user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user"
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
