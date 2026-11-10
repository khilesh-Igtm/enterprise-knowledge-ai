import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine
from app.integrations.qdrant import create_qdrant_client
from app.integrations.redis import create_redis_client

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.APP_NAME)

    redis_client = create_redis_client()
    qdrant_client = create_qdrant_client()

    app.state.redis = redis_client
    app.state.qdrant = qdrant_client

    try:
        # Verify PostgreSQL
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

        # Verify Redis
        await redis_client.ping()

        # Verify Qdrant
        await qdrant_client.get_collections()

        logger.info("PostgreSQL connected")
        logger.info("Redis connected")
        logger.info("Qdrant connected")

        yield

    finally:
        logger.info("Shutting down application")

        await redis_client.aclose()
        await qdrant_client.close()
        await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Enterprise Knowledge AI API",
        "docs": "/docs",
    }
