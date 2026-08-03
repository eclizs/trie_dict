from .models import User, Entry, Base

from sqlalchemy import Engine, event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///./entries.db"

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session



# async def run():
#     await init_db()

#     async with engine.connect() as conn:
#         result = await conn.exec_driver_sql("PRAGMA foreign_keys")
#         print(result.scalar())

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(run())