from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    PaginationParams,
    get_client_by_id,
    get_current_admin_client,
    get_db_session,
    paginate,
)
from app.models.clients import Client
from app.schemas.clients import (
    ClientCreate,
    ClientCreateResponse,
    ClientRead,
    ClientUpdate,
    ClientUpdateResponse,
)
from app.services.clients import service_client

router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
    dependencies=[Depends(get_current_admin_client)],
)


@router.post(
    "",
    response_model=ClientCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new client",
    description=(
        "Creates a new OAuth2 client and returns its generated credentials. "
        "The **client_secret** is included in this response **exactly once** "
        "and is never stored in plain text — store it securely immediately.\n\n"
        "Requires an active admin bearer token."
    ),
    response_description=(
        "The newly registered client, including its one-time ``client_secret``."
    ),
    responses={
        409: {
            "description": "A client with an identical ``oauth_id`` already "
            "exists (rare credential collision).",
        },
        500: {"description": "Unexpected persistence failure."},
    },
)
async def create_client(
    create_schema: ClientCreate,
    db_session: AsyncSession = Depends(get_db_session),
) -> ClientCreateResponse:
    """Register a new OAuth2 client.

    Generates a unique ``client_id`` / ``client_secret`` pair, hashes the
    secret, and persists the new client. The plaintext secret is returned
    once and cannot be retrieved again.

    Args:
        create_schema: Registration payload with ``name`` and optional
            ``is_admin`` flag.
        db_session: Injected async database session.

    Returns:
        A :class:`~app.schemas.clients.ClientCreateResponse` containing the
        new client's details and one-time credentials.

    Raises:
        HTTPException: ``409 Conflict`` on credential collision;
            ``500 Internal Server Error`` on unexpected failure.
    """
    return await service_client.new(db_session, create_schema)


@router.get(
    "",
    response_model=list[ClientRead],
    summary="List clients",
    description=(
        "Returns a paginated list of registered OAuth2 clients.\n\n"
        "Use the ``active_only`` query parameter to include soft-deleted "
        "clients in the results. Requires an active admin bearer token."
    ),
    response_description="A paginated list of client records.",
)
async def list_clients(
    pagination: Annotated[PaginationParams, Depends(paginate())],
    active_only: bool = Query(
        True,
        description="When true, only active clients are returned",
    ),
    db_session: AsyncSession = Depends(get_db_session),
) -> Sequence[Client]:
    """Return a paginated list of OAuth2 clients.

    Args:
        pagination: Resolved pagination parameters (``page``, ``per_page``).
        active_only: When ``True`` (default), soft-deleted clients are
            excluded from the results.
        db_session: Injected async database session.

    Returns:
        A list of :class:`~app.schemas.clients.ClientRead` objects.
    """
    return await service_client.get_many(
        db_session,
        pagination.page,
        pagination.per_page,
        active_only,
    )


@router.get(
    "/{id}",
    response_model=ClientRead,
    summary="Get a client by ID",
    description=(
        "Retrieves a single client record by its internal numeric ID.\n\n"
        "Requires an active admin bearer token."
    ),
    response_description="The requested client record.",
    responses={
        404: {"description": "No client found with the given ID."},
    },
)
async def get_client(
    client: Client = Depends(get_client_by_id),
) -> Client:
    """Retrieve a single client by its primary key.

    The client lookup and 404 handling are performed by the
    ``get_client_by_id`` dependency.

    Args:
        client: The resolved :class:`~app.models.clients.Client` ORM instance.

    Returns:
        The serialised :class:`~app.schemas.clients.ClientRead` representation.
    """
    return client


@router.patch(
    "/{id}",
    response_model=ClientUpdateResponse,
    summary="Update a client",
    description=(
        "Partially updates a client's attributes. All fields are optional.\n\n"
        "Set ``regenerate_credentials`` to ``true`` to rotate the client's "
        "``client_id`` and ``client_secret``. The new plaintext secret is "
        "included in the response **once only**.\n\n"
        "Requires an active admin bearer token."
    ),
    response_description=(
        "The updated client. ``client_id`` and ``client_secret`` are ``null`` "
        "when credentials were not regenerated."
    ),
    responses={
        404: {"description": "No client found with the given ID."},
        500: {"description": "Unexpected persistence failure."},
    },
)
async def update_client(
    update_schema: ClientUpdate,
    client: Client = Depends(get_client_by_id),
    db_session: AsyncSession = Depends(get_db_session),
) -> ClientUpdateResponse:
    """Apply a partial update to a client.

    Optionally rotates the client's OAuth2 credentials when
    ``regenerate_credentials`` is ``True``.

    Args:
        update_schema: Fields to update; at least one should differ from the
            current state to have any effect.
        client: The resolved :class:`~app.models.clients.Client` ORM instance.
        db_session: Injected async database session.

    Returns:
        A :class:`~app.schemas.clients.ClientUpdateResponse` with the updated
        state and new credentials (if rotated).

    Raises:
        HTTPException: ``500 Internal Server Error`` on unexpected failure.
    """
    return await service_client.admin_update(db_session, client, update_schema)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a client",
    description=(
        "Soft-deletes a client by recording a ``deleted_at`` timestamp. "
        "The record is retained in the database but excluded from "
        "active-only queries and can no longer authenticate.\n\n"
        "Requires an active admin bearer token."
    ),
    response_description="No content — the client has been deactivated.",
    responses={
        404: {"description": "No client found with the given ID."},
    },
)
async def deactivate_client(
    client: Client = Depends(get_client_by_id),
    db_session: AsyncSession = Depends(get_db_session),
) -> None:
    """Soft-delete a client.

    Sets ``deleted_at`` to the current UTC time. This operation is
    irreversible through the standard API surface.

    Args:
        client: The resolved :class:`~app.models.clients.Client` ORM instance.
        db_session: Injected async database session.
    """
    await service_client.deactivate(db_session, client)
