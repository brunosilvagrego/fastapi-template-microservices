from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clients import Client
from app.models.items import Item
from app.schemas.items import ItemCreate, ItemCreatePrivate, ItemUpdate
from app.services.crud import CRUDBase


class ItemService(CRUDBase[Item, ItemCreatePrivate, ItemUpdate]):
    async def new(
        self,
        db_session: AsyncSession,
        client: Client,
        create_schema: ItemCreate,
    ) -> Item:
        return await self.create(
            db_session,
            ItemCreatePrivate(
                **create_schema.model_dump(),
                owner_id=client.id,
            ),
        )

    async def update_check(
        self,
        db_session,
        item: Item,
        update_schema: ItemUpdate,
    ) -> Item:
        updated_item = await self.update(
            db_session,
            db_object=item,
            update_schema=update_schema,
        )

        if updated_item is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update item.",
            )

        return updated_item


service_item = ItemService(Item)
