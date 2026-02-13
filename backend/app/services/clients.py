from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import utils
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


async def get_all(db_session: AsyncSession) -> Sequence[Client]:
    stmt = select(Client)
    result = await db_session.execute(stmt)

    return result.scalars().all()


async def create(
    db_session: AsyncSession,
    name: str,
    oauth_id: str,
    oauth_secret_hash: str,
    is_admin: bool = False,
) -> Client:
    client = Client(
        name=name,
        created_at=utils.now_utc(),
        is_admin=is_admin,
        oauth_id=oauth_id,
        oauth_secret_hash=oauth_secret_hash,
    )

    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)

    return client
