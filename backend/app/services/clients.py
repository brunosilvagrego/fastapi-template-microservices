from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Client


async def get(db_session: AsyncSession, id: int) -> Client | None:
    stmt = select(Client).where(Client.id == id)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_oauth_id(
    db_session: AsyncSession,
    oauth_id: str | None,
) -> Client | None:
    if oauth_id is None:
        return None

    stmt = select(Client).where(Client.oauth_id == oauth_id)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()
