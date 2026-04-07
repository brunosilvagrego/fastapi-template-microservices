import pytest
from app.core.config import settings
from app.models.clients import Client
from app.schemas.clients import ClientCreate
from app.services.clients import service_client
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.utils import NONEXISTENT_ID

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

    client_id = client_data.get("id")
    assert isinstance(client_id, int)

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

    db_client = await service_client.get(db_session, id=client_id)
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
        )


async def create_new_client(
    http_client: AsyncClient,
    name: str,
    is_admin: bool,
    expected_status: status = status.HTTP_201_CREATED,
) -> dict:
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
) -> dict:
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
async def test_no_credentials(http_client: AsyncClient) -> None:
    await check_endpoints_access(
        http_client,
        headers={},
        expected_status=status.HTTP_401_UNAUTHORIZED,
    )


@pytest.mark.anyio
async def test_invalid_token(http_client: AsyncClient) -> None:
    await check_endpoints_access(
        http_client,
        headers={"Authorization": "Bearer invalid_token"},
        expected_status=status.HTTP_401_UNAUTHORIZED,
    )


@pytest.mark.anyio
async def test_external_client_access(
    http_client_external: AsyncClient,
) -> None:
    await check_endpoints_access(
        http_client_external,
        headers={},
        expected_status=status.HTTP_403_FORBIDDEN,
    )


# TODO: test 422 for invalid request data
@pytest.mark.anyio
@pytest.mark.parametrize(
    "name,is_admin",
    [
        ("Service A", True),
        ("Service B", False),
    ],
)
async def test_create_client(
    db_session: AsyncSession,
    http_client_admin: AsyncClient,
    name: str,
    is_admin: bool,
) -> None:
    client_data = await create_new_client(http_client_admin, name, is_admin)
    await check_client_data(
        db_session,
        client_data,
        name,
        is_admin,
        credentials=True,
    )


@pytest.mark.anyio
async def test_get_clients(
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

    await check_clients_list(
        db_session,
        clients_data=response.json(),
        expected_clients=expected_clients,
    )

    new_client = await service_client.new(
        db_session,
        create_schema=ClientCreate(
            name="Service A",
            is_admin=False,
        ),
    )
    assert new_client is not None
    expected_clients.append(new_client)

    response = await http_client_admin.get(API_CLIENTS_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK

    await check_clients_list(
        db_session,
        clients_data=response.json(),
        expected_clients=expected_clients,
    )


# TODO: test get after create
@pytest.mark.anyio
@pytest.mark.parametrize(
    "id,expected_name,expected_is_admin,expected_status",
    [
        (1, settings.ADMIN_CLIENT_NAME, True, status.HTTP_200_OK),
        (2, settings.EXTERNAL_CLIENT_NAME, False, status.HTTP_200_OK),
        (NONEXISTENT_ID, None, None, status.HTTP_404_NOT_FOUND),
        ("invalid_id", None, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_get_client_by_id(
    db_session: AsyncSession,
    http_client_admin: AsyncClient,
    id: int,
    expected_name: str,
    expected_is_admin: bool,
    expected_status: status,
) -> None:
    client_data = await get_client(http_client_admin, id, expected_status)

    if expected_status == status.HTTP_200_OK:
        await check_client_data(
            db_session,
            client_data,
            expected_name,
            expected_is_admin,
        )


# @pytest.mark.anyio
# async def test_update_client(http_client_admin: AsyncClient) -> None:
#     name = "Service D"
#     is_admin = False

#     original_data = await create_new_client(
#         client=http_client_admin,
#         name=name,
#         is_admin=is_admin,
#     )
#     check_client_data(original_data, name, is_admin, credentials=True)

#     id = original_data["id"]

#     # Update name
#     new_name = "Updated Service"

#     updated_data = await update_client(
#         client=http_client_admin,
#         id=id,
#         name=new_name,
#     )
#     check_client_data(updated_data, new_name, is_admin)

#     data = await get_client(http_client_admin, id)
#     check_client_data(data, new_name, is_admin)

#     # Update is_admin
#     for is_admin in [True, False]:
#         updated_data = await update_client(
#             client=http_client_admin,
#             id=id,
#             is_admin=is_admin,
#         )
#         check_client_data(updated_data, new_name, is_admin)

#         data = await get_client(http_client_admin, id)
#         check_client_data(data, new_name, is_admin)

#     # Update credentials
#     updated_data = await update_client(
#         client=http_client_admin,
#         id=id,
#         regenerate_credentials=True,
#     )
#     check_client_data(updated_data, new_name, is_admin, credentials=True)

#     data = await get_client(http_client_admin, id)
#     check_client_data(data, new_name, is_admin)

#     # Try to update a nonexistent client
#     await update_client(
#         client=http_client_admin,
#         id=NONEXISTENT_ID,
#         name=new_name,
#         expected_status=status.HTTP_404_NOT_FOUND,
#     )


# @pytest.mark.anyio
# async def test_delete_client(http_client_admin: AsyncClient) -> None:
#     clients_to_delete = []

#     for name, is_admin in [
#         ("Admin Service to Delete", True),
#         ("Service to Delete", False),
#     ]:
#         new_data = await create_new_client(
#             client=http_client_admin,
#             name=name,
#             is_admin=is_admin,
#         )
#         clients_to_delete.append(new_data)

#         data = await get_client(http_client_admin, new_data["id"])
#         check_client_data(data)

#     for client in clients_to_delete:
#         id = client["id"]

#         await delete_client(
#             client=http_client_admin,
#             id=id,
#             expected_status=status.HTTP_204_NO_CONTENT,
#         )

#         await get_client(
#             client=http_client_admin,
#             id=id,
#             expected_status=status.HTTP_400_BAD_REQUEST,
#         )

#         await delete_client(
#             client=http_client_admin,
#             id=id,
#             expected_status=status.HTTP_400_BAD_REQUEST,
#         )

#     # Try to delete a nonexistent client
#     await delete_client(
#         client=http_client_admin,
#         id=NONEXISTENT_ID,
#         expected_status=status.HTTP_404_NOT_FOUND,
#     )
