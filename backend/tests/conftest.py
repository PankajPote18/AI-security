"""API test fixtures: a real Postgres test database, truncated before every test for isolation,
and an httpx `AsyncClient` wired to the FastAPI app over ASGI transport (no running server, no
real network).

Deliberately does NOT fall back to `DATABASE_URL` if `TEST_DATABASE_URL` is unset: these fixtures
delete every row in every table before each test, so accidentally pointing that at the dev
database would destroy real data.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.db.session import get_db
from app.main import create_app
from app.models.user import User
from app.services import knowledge_service
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

_settings = get_settings()
if not _settings.test_database_url:
    raise RuntimeError(
        "TEST_DATABASE_URL is not set; refusing to run API tests without a dedicated test "
        "database (these fixtures truncate every table before each test)."
    )

# NullPool: a fresh connection per checkout, not a shared pool. Fixtures (db_session,
# existing_user) and the client's per-request dependency-injected session can be live at the
# same time; a pooled connection handed to both concurrently is what asyncpg's "another
# operation is in progress" error means.
_test_engine = create_async_engine(_settings.test_database_url, poolclass=NullPool)
_TestSessionFactory = async_sessionmaker(_test_engine, expire_on_commit=False)

# Child tables first, so foreign keys never block a delete.
_TABLES_IN_DELETE_ORDER = (
    "feedback",
    "security_reports",
    "predictions",
    "analyses",
    "domains",
    "urls",
    "users",
)


@pytest.fixture(scope="session", autouse=True)
def _ensure_knowledge_base_indexed() -> None:
    # httpx's ASGITransport never runs the app's lifespan, so unlike production the knowledge
    # base is not auto-ingested on startup - tests must not rely on it having been ingested by
    # some earlier local run (that state doesn't exist in a fresh CI checkout).
    knowledge_service.reingest()


@pytest_asyncio.fixture(autouse=True)
async def _clean_database() -> AsyncIterator[None]:
    async with _test_engine.begin() as conn:
        for table in _TABLES_IN_DELETE_ORDER:
            await conn.execute(text(f"DELETE FROM {table}"))  # noqa: S608 - fixed table names, not user input
    yield


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with _TestSessionFactory() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        async with _TestSessionFactory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client


@pytest_asyncio.fixture
async def existing_user(db_session: AsyncSession) -> User:
    user = User(email="existing@example.com", password_hash=hash_password("correct horse battery"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(existing_user: User) -> dict[str, str]:
    token = create_access_token(existing_user.id)
    return {"Authorization": f"Bearer {token}"}
