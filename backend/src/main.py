import ctypes
import re
import io
import asyncio

from typing import Annotated
from fastapi import status, Depends, FastAPI, Query, Request, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from .models import Entry, User

from .schema import EntryCreate

from .init import create_trie_root, init_trie
from .database import engine, Base, get_db
from .routers.users import Identity, get_identity, router, DatabaseSession
from .config import settings

from pandas import read_csv

re.ASCII

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    root, functions = init_trie()
    app.state.roots = {}
    app.state.root_locks = {}
    app.state.functions = functions

    yield

    destroyTrieNode = app.state.functions["destroyTrieNode"]
    for root in app.state.roots.values():
        destroyTrieNode(ctypes.byref(root))
    app.state.roots.clear()
    app.state.root_locks.clear()

    await engine.dispose()

app = FastAPI(lifespan=lifespan)

def get_or_create_root(app: FastAPI, identity: str):
    root = app.state.roots.get(identity)

    if root is not None:
        return root, False

    root = create_trie_root()
    app.state.roots[identity] = root

    return root, True

def discard_root(app: FastAPI, identity: str):
    root = app.state.roots.pop(identity, None)
    if root is not None:
        destroyTrieNode = app.state.functions["destroyTrieNode"]
        destroyTrieNode(ctypes.byref(root))

def get_root_lock(app: FastAPI, identity: str) -> asyncio.Lock:
    lock = app.state.root_locks.get(identity)

    if lock is None:
        lock = asyncio.Lock()
        app.state.root_locks[identity] = lock

    return lock

def get_user_id(identity: Identity):
    if identity.startswith("user:"):
        return int(identity.removeprefix("user:"))
    elif identity.startswith("guest:"):
        return -1
    else:
        raise ValueError("Invalid parameters")

async def populate_trie(
    request: Request,
    identity: Identity,
    session: DatabaseSession,
    root: ctypes._Pointer
):
    insertTrieNode = request.app.state.functions["insertTrieNode"]

    user_id = get_user_id(identity)
    results =  await session.execute(select(Entry).where(Entry.user_id == user_id))

    entries = results.scalars().all()

    for entry in entries:
        c_word = ctypes.create_string_buffer(entry.entry.encode("utf-8"))
        result = insertTrieNode(ctypes.byref(root), c_word)

        if result != status.HTTP_201_CREATED:
            raise RuntimeError(
                f"Could not load entry {entry.id} into the trie (status {result})"
            )

async def get_loaded_root(
    request: Request,
    identity: Identity,
    session: DatabaseSession,
):
    root, created = get_or_create_root(request.app, identity)

    if created and identity.startswith("user:"):
        try:
            await populate_trie(request, identity, session, root)
        except Exception:
            discard_root(request.app, identity)
            raise

    return root

@asynccontextmanager
async def locked_root(
    request: Request,
    identity: Identity,
    session: DatabaseSession,
):
    lock = get_root_lock(request.app, identity)

    async with lock:
        yield await get_loaded_root(request, identity, session)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key.get_secret_value(),
    max_age=24 * 60 * 60,
    same_site="lax",
    https_only=False
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.include_router(router, prefix="/users", tags=["users"])

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.get("/search")
async def search_word(
    request: Request,
    identity: Identity,
    session: DatabaseSession,
    prefix: Annotated[
        str | None, Query(max_length=100, pattern=r'^[-a-zA-Z0-9 /@"()+.,]*$')
    ] = None
):
    findWords = request.app.state.functions["findWords"]
    freeWordList = request.app.state.functions["freeWordList"]

    async with locked_root(request, identity, session) as root:
        if not prefix:
            prefix = ""

        c_prefix = ctypes.create_string_buffer(prefix.encode("utf-8"))
        word_list = findWords(root, c_prefix)

        response = []

        try:
            for i in range(word_list.count):
                entry = word_list.entries[i]
                response.append(entry.decode('utf-8'))
        finally:
            freeWordList(word_list)

    if response == []:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matches found")
    return {"words": response}

@app.post("/insert")
async def insert_word(
    request: Request,
    identity: Identity,
    session: DatabaseSession,
    word: Annotated[ str, Query(max_length=100, pattern=r'^[-a-zA-Z0-9 /@"()+.,]*$') ],
):
    async with locked_root(request, identity, session) as root:
        insertTrieNode = request.app.state.functions["insertTrieNode"]
        c_word = ctypes.create_string_buffer(word.encode("utf-8"))

        user_id = get_user_id(identity)
        if user_id != -1:
            entry = Entry(
                user_id=user_id,
                entry=word
            )
            session.add(entry)

            try:
                await session.flush()
            except IntegrityError:
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"'{word}' already exists"
                )
            except SQLAlchemyError:
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not save word"
                )

            result = insertTrieNode(ctypes.byref(root), c_word)

            if result != status.HTTP_201_CREATED:
                await session.rollback()
            else:
                try:
                    await session.commit()
                except SQLAlchemyError:
                    await session.rollback()
                    discard_root(request.app, identity)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Could not save word"
                    )
        else:
            result = insertTrieNode(ctypes.byref(root), c_word)

        if result == 400:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"'{word}' is empty")
        elif result == 409:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"'{word}' already exists")
        elif result == 201:
            return {"message": f"successfully inserted '{word}'"}
        else:
            discard_root(request.app, identity)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected response from trie"
            )
    

@app.post("/admin/insert_excel", include_in_schema=False)
async def insert_excel(
    request: Request,
    identity: Identity,
    session: DatabaseSession,
    file: UploadFile = File(...)
):
    user_id = get_user_id(identity)
    if user_id == -1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Method not allowed"
        )
    
    result = await session.execute(select(User).where(User.id == get_user_id(identity)))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User doesn't exists"
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Method not allowed"
        )
    
    contents = await file.read()
    df = read_csv(io.BytesIO(contents), header=None)

    fields = ['location', 'code', 'name', 'quantity', 'quantifier', 'total']

    df = df.set_axis(fields, axis=1)

    names = list(df['name'])

    names = [name.strip('"') if name.startswith('"') or name.endswith('"') else name
            for name in names]

    results = {"inserted": [], "failed": []}
    for name in names:
        try:
            await insert_word(request, identity, session, name)
            results["inserted"].append(name)
        except HTTPException as e:
            results["failed"].append({"word": name, "reason": e.detail})

    return results

@app.delete("/delete")
async def delete_word(
    request: Request,
    identity: Identity,
    session: DatabaseSession,
    word: Annotated[
        str, Query(max_length=100, pattern=r'^[-a-zA-Z0-9 /@"()+.,]*$')
    ],
):
    async with locked_root(request, identity, session) as root:
        deleteWord = request.app.state.functions["deleteWord"]
        c_word = ctypes.create_string_buffer(word.encode("utf-8"))

        user_id = get_user_id(identity)
        if user_id != -1:
            result = await session.execute(
                select(Entry).where(
                    Entry.user_id == user_id,
                    func.lower(Entry.entry) == word.lower(),
                )
            )
            entry = result.scalars().first()

            if entry is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"'{word}' not found"
                )
            await session.delete(entry)
            try:
                await session.flush()
            except SQLAlchemyError:
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not delete word"
                )

            result = deleteWord(ctypes.byref(root), c_word)

            if not result:
                await session.rollback()
                discard_root(request.app, identity)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Stored word could not be removed from the trie"
                )

            try:
                await session.commit()
            except SQLAlchemyError:
                await session.rollback()
                discard_root(request.app, identity)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not delete word"
                )
        else:
            result = deleteWord(ctypes.byref(root), c_word)

        if result == False:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"'{word}' not found")
        else:
            return {"message": f"successfully deleted '{word}'"}
