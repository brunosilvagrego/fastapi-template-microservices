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
)
async def create_client(
    create_schema: ClientCreate,
    db_session: AsyncSession = Depends(get_db_session),
) -> ClientCreateResponse:
    return await service_client.new(db_session, create_schema)


@router.get("", response_model=list[ClientRead])
async def list_clients(
    pagination: Annotated[PaginationParams, Depends(paginate())],
    active: bool = Query(
        True,
        description="When true, only active clients are returned",
    ),
    db_session: AsyncSession = Depends(get_db_session),
) -> Sequence[Client]:
    return await service_client.get_many(
        db_session,
        pagination.page,
        pagination.per_page,
        active,
    )


@router.get("/{id}", response_model=ClientRead)
async def get_client(
    client: Client = Depends(get_client_by_id),
) -> Client:
    return client


@router.patch("/{id}", response_model=ClientUpdateResponse)
async def update_client(
    update_schema: ClientUpdate,
    client: Client = Depends(get_client_by_id),
    db_session: AsyncSession = Depends(get_db_session),
) -> ClientUpdateResponse:
    return await service_client.admin_update(db_session, client, update_schema)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_client(
    client: Client = Depends(get_client_by_id),
    db_session: AsyncSession = Depends(get_db_session),
) -> None:
    await service_client.deactivate(db_session, client)
