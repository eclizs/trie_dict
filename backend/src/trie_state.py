import asyncio
import ctypes
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .dependencies import get_user_id
from .init import create_trie_root, init_trie
from .models import Entry


def initialize_trie_state(app: FastAPI) -> None:
    _, functions = init_trie()
    app.state.roots = {}
    app.state.root_locks = {}
    app.state.functions = functions


def destroy_trie_state(app: FastAPI) -> None:
    destroy_trie_node = app.state.functions["destroyTrieNode"]

    for root in app.state.roots.values():
        destroy_trie_node(ctypes.byref(root))

    app.state.roots.clear()
    app.state.root_locks.clear()


def get_or_create_root(app: FastAPI, identity: str):
    root = app.state.roots.get(identity)

    if root is not None:
        return root, False

    root = create_trie_root()
    app.state.roots[identity] = root

    return root, True


def discard_root(app: FastAPI, identity: str) -> None:
    root = app.state.roots.pop(identity, None)
    if root is not None:
        destroy_trie_node = app.state.functions["destroyTrieNode"]
        destroy_trie_node(ctypes.byref(root))


def get_root_lock(app: FastAPI, identity: str) -> asyncio.Lock:
    lock = app.state.root_locks.get(identity)

    if lock is None:
        lock = asyncio.Lock()
        app.state.root_locks[identity] = lock

    return lock


async def populate_trie(
    request: Request,
    identity: str,
    session: AsyncSession,
    root: ctypes._Pointer,
) -> None:
    insert_trie_node = request.app.state.functions["insertTrieNode"]
    results = await session.execute(
        select(Entry).where(Entry.user_id == get_user_id(identity))
    )

    for entry in results.scalars().all():
        c_word = ctypes.create_string_buffer(entry.entry.encode("utf-8"))
        result = insert_trie_node(ctypes.byref(root), c_word)

        if result != status.HTTP_201_CREATED:
            raise RuntimeError(
                f"Could not load entry {entry.id} into the trie (status {result})"
            )


async def get_loaded_root(
    request: Request,
    identity: str,
    session: AsyncSession,
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
    identity: str,
    session: AsyncSession,
):
    lock = get_root_lock(request.app, identity)

    async with lock:
        yield await get_loaded_root(request, identity, session)
