from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    PaginationParams,
    get_current_client,
    get_db_session,
    get_item_by_id,
    paginate,
)
from app.models.clients import Client
from app.models.items import Item
from app.schemas.items import ItemCreate, ItemRead, ItemUpdate
from app.services.items import service_item

router = APIRouter(
    prefix="/items",
    tags=["Items"],
    dependencies=[Depends(get_current_client)],
)


@router.post(
    "",
    response_model=ItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an item",
    description=(
        "Creates a new item owned by the currently authenticated client. "
        "The ``owner_id`` is derived from the bearer token and cannot be "
        "specified in the request body.\n\n"
        "Requires a valid bearer token."
    ),
    response_description="The newly created item.",
)
async def create_item(
    create_schema: ItemCreate,
    client: Client = Depends(get_current_client),
    db_session: AsyncSession = Depends(get_db_session),
) -> Item:
    """Create a new item for the authenticated client.

    Args:
        create_schema: Item creation payload containing ``title`` and
            ``description``.
        client: The authenticated :class:`~app.models.clients.Client`; its
            ``id`` is used as the item's ``owner_id``.
        db_session: Injected async database session.

    Returns:
        The newly created :class:`~app.models.items.Item` ORM instance,
        serialised as :class:`~app.schemas.items.ItemRead`.
    """
    return await service_item.new(db_session, client, create_schema)


@router.get(
    "",
    response_model=list[ItemRead],
    summary="List items",
    description=(
        "Returns a paginated list of items belonging to the authenticated "
        "client. Items owned by other clients are never included.\n\n"
        "Requires a valid bearer token."
    ),
    response_description="A paginated list of the client's items.",
)
async def list_items(
    pagination: Annotated[PaginationParams, Depends(paginate())],
    client: Client = Depends(get_current_client),
    db_session: AsyncSession = Depends(get_db_session),
) -> Sequence[Item]:
    """Return a paginated list of items owned by the authenticated client.

    Args:
        pagination: Resolved pagination parameters (``page``, ``per_page``).
        client: The authenticated :class:`~app.models.clients.Client` used to
            filter results by ``owner_id``.
        db_session: Injected async database session.

    Returns:
        A list of :class:`~app.schemas.items.ItemRead` objects.
    """
    return await service_item.get_multi(
        db_session,
        page=pagination.page,
        per_page=pagination.per_page,
        owner_id=client.id,
    )


@router.get(
    "/{id}",
    response_model=ItemRead,
    summary="Get an item by ID",
    description=(
        "Retrieves a single item by its internal numeric ID.\n\n"
        "Requires a valid bearer token."
    ),
    response_description="The requested item.",
    responses={
        404: {"description": "No item found with the given ID."},
    },
)
async def get_item(
    item: Item = Depends(get_item_by_id),
) -> Item:
    """Retrieve a single item by its primary key.

    The item lookup and 404 handling are performed by the ``get_item_by_id``
    dependency.

    Args:
        item: The resolved :class:`~app.models.items.Item` ORM instance.

    Returns:
        The serialised :class:`~app.schemas.items.ItemRead` representation.
    """
    return item


@router.patch(
    "/{id}",
    response_model=ItemRead,
    summary="Update an item",
    description=(
        "Partially updates an item's ``title`` and/or ``description``. At "
        "least one field must be provided.\n\n"
        "Requires a valid bearer token."
    ),
    response_description="The updated item.",
    responses={
        404: {"description": "No item found with the given ID."},
        422: {
            "description": "Validation error — all fields were ``null`` or "
            "the payload was otherwise invalid.",
        },
        500: {"description": "Unexpected persistence failure."},
    },
)
async def update_item(
    update_schema: ItemUpdate,
    item: Item = Depends(get_item_by_id),
    db_session: AsyncSession = Depends(get_db_session),
) -> Item:
    """Apply a partial update to an item.

    At least one field in the payload must be non-``None`` (enforced by
    :class:`~app.schemas.base.NonEmptyModel`).

    Args:
        update_schema: Fields to update (``title`` and/or ``description``).
        item: The resolved :class:`~app.models.items.Item` ORM instance.
        db_session: Injected async database session.

    Returns:
        The updated :class:`~app.models.items.Item` ORM instance.

    Raises:
        HTTPException: ``500 Internal Server Error`` on unexpected failure.
    """
    return await service_item.update_check(db_session, item, update_schema)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an item",
    description=(
        "Permanently removes an item from the database.\n\n"
        "Requires a valid bearer token."
    ),
    response_description="No content — the item has been deleted.",
    responses={
        404: {"description": "No item found with the given ID."},
    },
)
async def delete_item(
    item: Item = Depends(get_item_by_id),
    db_session: AsyncSession = Depends(get_db_session),
) -> None:
    """Permanently delete an item.

    Unlike client deactivation, this is a hard delete — the record is removed
    from the database entirely.

    Args:
        item: The resolved :class:`~app.models.items.Item` ORM instance.
        db_session: Injected async database session.
    """
    await service_item.delete(db_session, db_object=item)
