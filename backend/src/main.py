import ctypes
import re
import io

from typing import Annotated
from fastapi import Depends, FastAPI, Query, Request, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm

from contextlib import asynccontextmanager

from backend.src.routers import users

from .init import init_trie
from .auth import create_access_token, oauth2_scheme, verify_access_token
from .models import User, Entry
from .config import get_settings
from .database import get_db, engine, Base
from .routers import entries, users

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from pandas import read_csv

re.ASCII

# DatabaseSession = Annotated[db.AsyncSession, Depends(db.get_db)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    root, functions = init_trie()
    app.state.root = root
    app.state.functions = functions

    # DatabaseSession = db.get_db()

    # result = DatabaseSession.execute

    yield

    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(entries.router, prefix="/entries", tags=["entries"])

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.get("/search")
async def search_word(request: Request, prefix: Annotated[ str | None, Query(max_length=100, pattern=r'^[-a-zA-Z0-9 /@"()+.,]*$') ] = None,):
    findWords = request.app.state.functions["findWords"]
    freeWordList = request.app.state.functions["freeWordList"]

    root = request.app.state.root

    if not prefix:
        prefix = ""

    word_list = findWords(root, prefix.encode('utf-8'))

    response = []
    
    for i in range(word_list.count):
        entry = word_list.entries[i]
        response.append(entry.decode('utf-8'))
        
    freeWordList(word_list)
    if response == []:
        raise HTTPException(status_code=404, detail="No matches found")
    return {"words": response}

@app.post("/insert")
async def insert_word(word: Annotated[ str, Query(max_length=100, pattern=r'^[-a-zA-Z0-9 /@"()+.,]*$') ], request: Request):
    insertTrieNode = request.app.state.functions["insertTrieNode"]
    root = request.app.state.root

    c_word = word.encode('utf-8')

    result = insertTrieNode(ctypes.byref(root), c_word)

    if result == 400:
        raise HTTPException(status_code=400, detail=f"'{word}' is empty")
    elif result == 409:
        raise HTTPException(status_code=409, detail=f"'{word}' already exists")
    elif result == 201:
        return {"message": f"successfully inserted '{word}'"}
    

@app.post("/insert_excel", include_in_schema=False)
async def insert_excel(request: Request, file: UploadFile = File(...)):
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
            await insert_word(name, request)
            results["inserted"].append(name)
        except HTTPException as e:
            results["failed"].append({"word": name, "reason": e.detail})

    return results

@app.delete("/delete")
async def delete_word(word: Annotated[ str, Query(max_length=100, pattern=r'^[-a-zA-Z0-9 /@"()+.,]*$') ], request: Request):
    deleteWord = request.app.state.functions["deleteWord"]
    root = request.app.state.root

    c_word = word.encode('utf-8')

    result = deleteWord(ctypes.byref(root), c_word)

    if result == False:
        raise HTTPException(status_code=404, detail=f"'{word}' not found")
    else:
        return {"message": f"successfully deleted '{word}'"}
