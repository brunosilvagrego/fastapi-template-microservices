from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clients import Client
from app.models.items import Item
from app.schemas.items import ItemCreate, ItemCreatePrivate, ItemUpdate
from app.services.crud import CRUDBase


class ItemService(CRUDBase[Item, ItemCreatePrivate, ItemUpdate]):
    """Service layer for ``Item`` management.

    Extends :class:`~app.services.crud.CRUDBase` with business logic that
    associates items with their owning client and provides safe update
    semantics.
    """

    async def new(
        self,
        db_session: AsyncSession,
        client: Client,
        create_schema: ItemCreate,
    ) -> Item:
        """Create a new item owned by the authenticated client.

        Enriches the public creation payload with the resolved ``owner_id``
        before persisting the record.

        Args:
            db_session: The active async database session.
            client: The authenticated :class:`~app.models.clients.Client`
                whose ``id`` will be set as the item's ``owner_id``.
            create_schema: Public-facing creation payload containing the item
                ``title`` and ``description``.

        Returns:
            The newly created :class:`~app.models.items.Item` ORM instance.
        """
        return await self.create(
            db_session,
            ItemCreatePrivate(
                **create_schema.model_dump(),
                owner_id=client.id,
            ),
        )

    async def update_check(
        self,
        db_session: AsyncSession,
        item: Item,
        update_schema: ItemUpdate,
    ) -> Item:
        """Update an item and raise an error if the operation fails.

        Wraps :meth:`~app.services.crud.CRUDBase.update` with an explicit
        ``None``-check so that callers always receive a valid instance or a
        clear HTTP error rather than having to handle ``None`` themselves.

        Args:
            db_session: The active async database session.
            item: The :class:`~app.models.items.Item` ORM instance to update.
            update_schema: Update payload; at least one field must be set
                (enforced by :class:`~app.schemas.base.NonEmptyModel`).

        Returns:
            The updated :class:`~app.models.items.Item` ORM instance.

        Raises:
            HTTPException: ``500 Internal Server Error`` if the underlying
                update returns ``None``.
        """
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
