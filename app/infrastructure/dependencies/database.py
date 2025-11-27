"""Database dependency providers for FastAPI."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as aioredis

from app.db.session import async_session
from app.infrastructure.config import get_settings


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide database session for dependency injection.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        >>> @app.get("/items")
        >>> async def get_items(db: AsyncSession = Depends(get_db)):
        >>>     result = await db.execute(select(Item))
        >>>     return result.scalars().all()
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_mongodb() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Provide MongoDB database for dependency injection.

    Yields:
        AsyncIOMotorDatabase: Motor async MongoDB database

    Example:
        >>> @app.get("/messages")
        >>> async def get_messages(db: AsyncIOMotorDatabase = Depends(get_mongodb)):
        >>>     messages = await db.chat_messages.find().to_list(100)
        >>>     return messages
    """
    settings = get_settings()
    client = AsyncIOMotorClient(settings.database.mongodb_uri)
    db = client[settings.database.mongodb_database_name]

    try:
        yield db
    finally:
        client.close()


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Provide Redis client for dependency injection.

    Yields:
        aioredis.Redis: Async Redis client

    Example:
        >>> @app.get("/cache")
        >>> async def get_cached(redis: aioredis.Redis = Depends(get_redis)):
        >>>     value = await redis.get("key")
        >>>     return {"value": value}
    """
    settings = get_settings()
    redis_client = aioredis.from_url(
        settings.database.redis_url,
        decode_responses=settings.database.redis_decode_responses,
        max_connections=settings.database.redis_max_connections
    )

    try:
        yield redis_client
    finally:
        await redis_client.close()
