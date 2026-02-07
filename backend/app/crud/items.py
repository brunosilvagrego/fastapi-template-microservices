from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.items import Item
from app.schemas.items import ItemCreate, ItemUpdate


async def create_item(
    session: AsyncSession, item_in: ItemCreate, owner_id: int
) -> Item:
    db_item = Item(**item_in.model_dump(), owner_id=owner_id)
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item


async def get_items(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[Item]:
    statement = select(Item).offset(skip).limit(limit)
    result = await session.execute(statement)
    return result.scalars().all()


async def get_item(session: AsyncSession, item_id: int) -> Item | None:
    return await session.get(Item, item_id)


async def update_item(
    session: AsyncSession, db_item: Item, item_in: ItemUpdate
) -> Item:
    item_data = item_in.model_dump(exclude_unset=True)
    for key, value in item_data.items():
        setattr(db_item, key, value)
    
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item


async def delete_item(session: AsyncSession, db_item: Item) -> Item:
    await session.delete(db_item)
    await session.commit()
    return db_item
