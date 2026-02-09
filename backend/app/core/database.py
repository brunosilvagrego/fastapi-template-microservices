import asyncio
import socket

from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

url = URL.create(
    drivername="postgresql+asyncpg",  # asynchronous postgres driver
    username=settings.DB_USERNAME,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_DATABASE,
)

engine = create_async_engine(url)

SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)


async def db_health_check(timeout_seconds: float = 1.0) -> bool:
    """Check if the database is up. Returns True if the database is healthy,
    False otherwise."""
    try:
        async with SessionLocal() as db_session:
            await asyncio.wait_for(
                db_session.execute(text("SELECT 1")),
                timeout=timeout_seconds,
            )
    except TimeoutError, socket.gaierror:
        return False

    return True
