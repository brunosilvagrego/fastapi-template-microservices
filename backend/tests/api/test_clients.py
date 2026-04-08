import pytest
from app.core.config import settings
from app.models.clients import Client
from app.schemas.clients import ClientCreate
from app.services.clients import service_client
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests import utils

API_CLIENTS_ENDPOINT = "/api/v1/clients"
API_CLIENT_ID_ENDPOINT = "/api/v1/clients/{id}"


async def check_endpoints_access(
    http_client: AsyncClient,
    headers: dict,
    expected_status: status,
) -> None:
    for request_func in [http_client.post, http_client.get]:
        response = await request_func(API_CLIENTS_ENDPOINT, headers=headers)
        assert response.status_code == expected_status

    client_id_url = API_CLIENT_ID_ENDPOINT.format(id=1)
    for request_func in [
        http_client.get,
        http_client.patch,
        http_client.delete,
    ]:
        response = await request_func(client_id_url, headers=headers)
        assert response.status_code == expected_status


async def check_client_data(
    db_session: AsyncSession,
    client_data: dict,
    expected_name: str,
    expected_is_admin: bool,
    deleted: bool = False,
    credentials: bool = False,
) -> None:
    assert isinstance(client_data, dict)

    id = client_data.get("id")
    assert isinstance(id, int)

    name = client_data.get("name")
    assert isinstance(name, str)
    assert name == expected_name

    assert isinstance(client_data.get("created_at"), str)

    deleted_at = client_data.get("deleted_at")
    if deleted:
        assert isinstance(deleted_at, (str))
    else:
        assert deleted_at is None

    is_admin = client_data.get("is_admin")
    assert isinstance(is_admin, bool)
    assert is_admin == expected_is_admin

    client_oauth_id = client_data.get("client_id")
    client_oauth_secret = client_data.get("client_secret")

    if credentials:
        assert isinstance(client_oauth_id, str)
        assert isinstance(client_oauth_secret, str)
    else:
        assert client_oauth_id is None
        assert client_oauth_secret is None

    db_client = await service_client.get(db_session, id=id)
    assert db_client is not None
    assert db_client.name == expected_name
    assert db_client.is_admin == expected_is_admin


async def check_clients_list(
    db_session: AsyncSession,
    clients_data: list[dict],
    expected_clients: list[Client],
) -> None:
    assert isinstance(clients_data, list)
    assert len(clients_data) == len(expected_clients)

    for client_data, expected_client in zip(
        clients_data,
        expected_clients,
        strict=True,
    ):
        await check_client_data(
            db_session,
            client_data=client_data,
            expected_name=expected_client.name,
            expected_is_admin=expected_client.is_admin,
            deleted=expected_client.deleted_at is not None,
        )


async def create_new_client(
    http_client: AsyncClient,
    name: str,
    is_admin: bool,
    expected_status: status = status.HTTP_201_CREATED,
) -> dict | None:
    response = await http_client.post(
        API_CLIENTS_ENDPOINT,
        json={"name": name, "is_admin": is_admin},
    )
    assert response.status_code == expected_status

    if expected_status != status.HTTP_201_CREATED:
        return None

    return response.json()


async def get_client(
    http_client: AsyncClient,
    id: int,
    expected_status: status = status.HTTP_200_OK,
) -> dict | None:
    response = await http_client.get(API_CLIENT_ID_ENDPOINT.format(id=id))
    assert response.status_code == expected_status

    if expected_status != status.HTTP_200_OK:
        return None

    return response.json()


async def update_client(
    http_client: AsyncClient,
    id: int,
    name: str | None = None,
    is_admin: bool | None = None,
    regenerate_credentials: bool | None = None,
    expected_status: status = status.HTTP_200_OK,
) -> dict | None:
    update_data = {}

    for key, value in (
        ("name", name),
        ("is_admin", is_admin),
        ("regenerate_credentials", regenerate_credentials),
    ):
        if value is not None:
            update_data[key] = value

    response = await http_client.patch(
        url=API_CLIENT_ID_ENDPOINT.format(id=id),
        json=update_data,
    )
    assert response.status_code == expected_status

    if expected_status != status.HTTP_200_OK:
        return None

    return response.json()


async def delete_client(
    http_client: AsyncClient,
    id: int,
    expected_status: status = status.HTTP_204_NO_CONTENT,
) -> None:
    response = await http_client.delete(API_CLIENT_ID_ENDPOINT.format(id=id))
    assert response.status_code == expected_status


@pytest.mark.anyio
async def test_client_endpoints_no_credentials(http_client: AsyncClient) -> None:
    await check_endpoints_access(
        http_client,
        headers={},
        expected_status=status.HTTP_401_UNAUTHORIZED,
    )


@pytest.mark.anyio
async def test_client_endpoints_invalid_token(http_client: AsyncClient) -> None:
    await check_endpoints_access(
        http_client,
        headers=utils.get_auth_header_invalid_token(),
        expected_status=status.HTTP_401_UNAUTHORIZED,
    )


@pytest.mark.anyio
async def test_client_endpoints_expired_token(http_client: AsyncClient) -> None:
    await check_endpoints_access(
        http_client,
        headers=utils.get_auth_header_expired_token(),
        expected_status=status.HTTP_401_UNAUTHORIZED,
    )


@pytest.mark.anyio
async def test_client_endpoints_external_access(
    http_client_external: AsyncClient,
) -> None:
    await check_endpoints_access(
        http_client_external,
        headers={},
        expected_status=status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "name,is_admin,expected_status",
    [
        ("Service B", True, status.HTTP_201_CREATED),
        ("Service C", False, status.HTTP_201_CREATED),
        ("", True, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (None, True, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("Service D", None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (5, True, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("Service D", 5, status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_create_client(
    db_session: AsyncSession,
    http_client_admin: AsyncClient,
    name: str | int | None,
    is_admin: bool | int | None,
    expected_status: status,
) -> None:
    client_data = await create_new_client(
        http_client_admin,
        name,
        is_admin,
        expected_status,
    )

    if expected_status == status.HTTP_201_CREATED:
        await check_client_data(
            db_session,
            client_data,
            name,
            is_admin,
            credentials=True,
        )


@pytest.mark.anyio
async def test_list_clients(
    db_session: AsyncSession,
    http_client_admin: AsyncClient,
) -> None:
    expected_clients = []

    for name in (settings.ADMIN_CLIENT_NAME, settings.EXTERNAL_CLIENT_NAME):
        client = await service_client.get(db_session, name=name)
        assert client is not None
        expected_clients.append(client)

    response = await http_client_admin.get(API_CLIENTS_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK

    # Check initial clients list
    await check_clients_list(
        db_session,
        clients_data=response.json(),
        expected_clients=expected_clients,
    )

    # Check list after adding a new client
    client_schema = await service_client.new(
        db_session,
        create_schema=ClientCreate(
            name="Service B",
            is_admin=False,
        ),
    )
    new_client = await service_client.get(db_session, id=client_schema.id)
    assert new_client is not None
    expected_clients.append(new_client)

    response = await http_client_admin.get(API_CLIENTS_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK

    await check_clients_list(
        db_session,
        clients_data=response.json(),
        expected_clients=expected_clients,
    )

    # Check list after deactivating a client
    await service_client.deactivate(db_session, client=new_client)
    expected_clients.pop()

    response = await http_client_admin.get(API_CLIENTS_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK

    await check_clients_list(
        db_session,
        clients_data=response.json(),
        expected_clients=expected_clients,
    )

    response = await http_client_admin.get(
        API_CLIENTS_ENDPOINT,
        params={"active_only": False},
    )
    assert response.status_code == status.HTTP_200_OK
    expected_clients.append(new_client)

    await check_clients_list(
        db_session,
        clients_data=response.json(),
        expected_clients=expected_clients,
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "id,expected_name,expected_is_admin",
    [
        (1, settings.ADMIN_CLIENT_NAME, True),
        (2, settings.EXTERNAL_CLIENT_NAME, False),
    ],
)
async def test_get_client(
    db_session: AsyncSession,
    http_client_admin: AsyncClient,
    id: int | str,
    expected_name: str,
    expected_is_admin: bool,
) -> None:
    client_data = await get_client(http_client_admin, id)

    await check_client_data(
        db_session,
        client_data,
        expected_name,
        expected_is_admin,
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "id,name,is_admin,regenerate_credentials,expected_status",
    [
        (2, "Service B", None, None, status.HTTP_200_OK),
        (2, None, True, None, status.HTTP_200_OK),
        (2, None, False, None, status.HTTP_200_OK),
        (2, None, None, True, status.HTTP_200_OK),
        (2, "Service C", True, True, status.HTTP_200_OK),
        (2, "", True, True, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (2, "Service D", 5, True, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (2, "Service D", True, 5, status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_update_client(
    db_session: AsyncSession,
    http_client_admin: AsyncClient,
    id: int | str,
    name: str | None,
    is_admin: bool | None,
    regenerate_credentials: bool | None,
    expected_status: status,
) -> None:
    updated_data = await update_client(
        http_client_admin,
        id,
        name,
        is_admin,
        regenerate_credentials,
        expected_status,
    )

    if expected_status == status.HTTP_200_OK:
        await check_client_data(
            db_session,
            client_data=updated_data,
            expected_name=name or settings.EXTERNAL_CLIENT_NAME,
            expected_is_admin=is_admin or False,
            credentials=regenerate_credentials,
        )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "name,is_admin",
    [
        ("Admin Service to Delete", True),
        ("Service to Delete", False),
    ],
)
async def test_delete_client(
    db_session: AsyncSession,
    http_client_admin: AsyncClient,
    name: str | None,
    is_admin: bool | None,
) -> None:
    client_schema = await service_client.new(
        db_session,
        create_schema=ClientCreate(
            name=name,
            is_admin=is_admin,
        ),
    )
    assert client_schema is not None

    await get_client(
        http_client_admin,
        id=client_schema.id,
        expected_status=status.HTTP_200_OK,
    )

    await delete_client(
        http_client_admin,
        id=client_schema.id,
        expected_status=status.HTTP_204_NO_CONTENT,
    )

    await get_client(
        http_client_admin,
        id=client_schema.id,
        expected_status=status.HTTP_400_BAD_REQUEST,
    )

    await delete_client(
        http_client_admin,
        id=client_schema.id,
        expected_status=status.HTTP_400_BAD_REQUEST,
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "id,expected_status",
    [
        (utils.NONEXISTENT_ID, status.HTTP_404_NOT_FOUND),
        ("invalid_id", status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_client_invalid_ids(
    http_client_admin: AsyncClient,
    id: int | str,
    expected_status: status,
) -> None:
    await get_client(http_client_admin, id, expected_status)

    await update_client(
        http_client_admin,
        id=id,
        name="New Name",
        is_admin=True,
        regenerate_credentials=True,
        expected_status=expected_status,
    )

    await delete_client(http_client_admin, id, expected_status)
