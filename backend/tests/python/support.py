import os
import sqlite3
import tempfile
import unittest
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)

os.environ.setdefault(
    "SECRET_KEY",
    "python-test-suite-secret-key-not-for-production",
)

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.src import database, main


class AppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "test.db"
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.database_path}"
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )

        self.original_engine = main.engine
        self.original_session_factory = database.AsyncSessionLocal
        main.engine = self.engine
        database.AsyncSessionLocal = self.session_factory

        self.client = TestClient(main.app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        main.engine = self.original_engine
        database.AsyncSessionLocal = self.original_session_factory
        self.temp_directory.cleanup()

    def database_rows(
        self,
        query: str,
        parameters: tuple = (),
    ) -> list[tuple]:
        connection = sqlite3.connect(self.database_path)
        try:
            return connection.execute(query, parameters).fetchall()
        finally:
            connection.close()

    def execute_sql(self, query: str, parameters: tuple = ()) -> None:
        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(query, parameters)
            connection.commit()
        finally:
            connection.close()

    def register(
        self,
        email: str = "user@example.com",
        password: str = "password123",
    ):
        return self.client.post(
            "/users/register",
            json={"email": email, "password": password},
        )

    def login(
        self,
        email: str = "user@example.com",
        password: str = "password123",
    ):
        return self.client.post(
            "/users/login",
            json={"email": email, "password": password},
        )

    def identity_with_prefix(self, prefix: str) -> str:
        return next(
            identity
            for identity in main.app.state.roots
            if identity.startswith(prefix)
        )
