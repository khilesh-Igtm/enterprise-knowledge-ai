import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

import app.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest_asyncio.fixture
async def client():
    database_url = settings.test_database_url

    if not database_url:
        raise RuntimeError(
            "TEST_DATABASE_URL must be configured before running tests"
        )

    if not database_url.startswith("postgresql+asyncpg://"):
        raise RuntimeError(
            "Tests require a PostgreSQL async connection"
        )

    database_name = make_url(database_url).database

    if database_name != "enterprise_knowledge_ai_test":
        raise RuntimeError(
            "Refusing to run destructive test fixtures "
            "against a non-test database"
        )

    engine = create_async_engine(database_url)

    TestSessionLocal = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await engine.dispose()