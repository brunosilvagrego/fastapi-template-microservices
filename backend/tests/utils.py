from datetime import timedelta

from app.core.config import settings
from app.core.security import create_access_token
from app.models.items import Item
from app.schemas.items import ItemCreatePrivate
from app.services.clients import service_client
from app.services.items import service_item
from fastapi import status
from httpx import AsyncClient

NONEXISTENT_ID = 999_999_999


def get_auth_request_data(client_id: str, client_secret: str) -> dict[str, str]:
    return {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }


async def get_client_token(
    client: AsyncClient,
    client_id: str,
    client_secret: str,
) -> str:
    response = await client.post(
        "/api/auth/token",
        data=get_auth_request_data(client_id, client_secret),
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()["access_token"]


def get_auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def make_authenticated_client(
    client: AsyncClient,
    client_id: str,
    client_secret: str,
) -> AsyncClient:
    token = await get_client_token(client, client_id, client_secret)
    client.headers.update(get_auth_header(token))
    return client


def get_auth_header_invalid_token() -> dict[str, str]:
    return get_auth_header("invalid_token")


def get_auth_header_expired_token(
    client_oauth_id: str | None = None,
) -> dict[str, str]:
    client_oauth_id = client_oauth_id or settings.ADMIN_CLIENT_ID

    expired_token = create_access_token(
        data={"sub": client_oauth_id},
        expire_delta=-timedelta(minutes=5),
    )

    return get_auth_header(expired_token)


async def create_item(
    db_session,
    client_oauth_id: str,
    title: str = "Item 1",
    description: str = "Description 1",
) -> Item:
    client = await service_client.get(db_session, oauth_id=client_oauth_id)

    return await service_item.create(
        db_session,
        create_schema=ItemCreatePrivate(
            title=title,
            description=description,
            owner_id=client.id,
        ),
    )


async def create_items(
    db_session,
    client_oauth_id: str,
    count: int,
) -> list[Item]:
    db_items: list[Item] = []

    for i in range(count):
        db_item = await create_item(
            db_session,
            client_oauth_id=client_oauth_id,
            title=f"Item {i}",
            description=f"Description {i}",
        )
        db_items.append(db_item)

    return db_items
