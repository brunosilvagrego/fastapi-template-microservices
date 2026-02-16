import pytest
from fastapi import status
from httpx import AsyncClient

API_CLIENTS_ENDPOINT = "/api/v1/clients"
API_CLIENT_ID_ENDPOINT = "/api/v1/clients/{id}"


async def check_endpoints_access(
    client: AsyncClient,
    headers: dict,
    expected_status: status,
) -> None:
    for request_func in [client.post, client.get]:
        response = await request_func(API_CLIENTS_ENDPOINT, headers=headers)
        assert response.status_code == expected_status

    client_id_url = API_CLIENT_ID_ENDPOINT.format(id=1)
    for request_func in [client.get, client.patch, client.delete]:
        response = await request_func(client_id_url, headers=headers)
        assert response.status_code == expected_status


@pytest.mark.anyio
async def test_no_credentials(client: AsyncClient) -> None:
    await check_endpoints_access(
        client,
        headers={},
        expected_status=status.HTTP_401_UNAUTHORIZED,
    )


@pytest.mark.anyio
async def test_invalid_token(client: AsyncClient) -> None:
    await check_endpoints_access(
        client,
        headers={"Authorization": "Bearer invalid_token"},
        expected_status=status.HTTP_401_UNAUTHORIZED,
    )


@pytest.mark.anyio
async def test_external_client_access(
    authenticated_external_client: AsyncClient,
) -> None:
    await check_endpoints_access(
        authenticated_external_client,
        headers={},
        expected_status=status.HTTP_403_FORBIDDEN,
    )


def check_client_data(
    client_data: dict,
    expected_name: str | None = None,
    expected_is_admin: bool | None = None,
    deleted: bool = False,
    credentials: bool = False,
) -> None:
    assert isinstance(client_data, dict)
    assert isinstance(client_data.get("id"), int)
    assert isinstance(client_data.get("name"), str)
    assert isinstance(client_data.get("created_at"), str)
    assert isinstance(client_data.get("is_admin"), bool)
    assert "deleted_at" in client_data

    if expected_name is not None:
        assert client_data["name"] == expected_name

    if expected_is_admin is not None:
        assert client_data["is_admin"] == expected_is_admin

    deleted_at = client_data.get("deleted_at")

    if deleted:
        assert isinstance(deleted_at, (str))
    else:
        assert deleted_at is None

    client_id = client_data.get("client_id")
    client_secret = client_data.get("client_secret")

    if credentials:
        assert isinstance(client_id, str)
        assert isinstance(client_secret, str)
    else:
        assert client_id is None
        assert client_secret is None


@pytest.mark.anyio
async def test_get_clients(
    authenticated_admin_client: AsyncClient,
) -> None:
    response = await authenticated_admin_client.get(API_CLIENTS_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    print(data)
    assert isinstance(data, list)
    assert len(data) > 0

    for client_data in data:
        check_client_data(client_data)


@pytest.mark.anyio
async def test_get_client_by_id(
    authenticated_admin_client: AsyncClient,
) -> None:
    for id in (1, 2, 3):
        expected_status = (
            status.HTTP_404_NOT_FOUND if id == 3 else status.HTTP_200_OK
        )

        response = await authenticated_admin_client.get(
            API_CLIENT_ID_ENDPOINT.format(id=id)
        )
        assert response.status_code == expected_status

        if expected_status == status.HTTP_200_OK:
            check_client_data(response.json())


async def create_new_client(
    authenticated_admin_client: AsyncClient,
    name: str,
    is_admin: bool,
) -> dict:
    response = await authenticated_admin_client.post(
        API_CLIENTS_ENDPOINT,
        json={"name": name, "is_admin": is_admin},
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


@pytest.mark.anyio
async def test_create_client(
    authenticated_admin_client: AsyncClient,
) -> None:
    for name, is_admin in [("Service B", True), ("Service C", False)]:
        data = await create_new_client(
            authenticated_admin_client,
            name=name,
            is_admin=is_admin,
        )

        check_client_data(
            data,
            expected_name=name,
            expected_is_admin=is_admin,
            credentials=True,
        )


async def update_client(
    authenticated_admin_client: AsyncClient,
    url: str,
    name: str | None = None,
    is_admin: bool | None = None,
    regenerate_credentials: bool | None = None,
) -> dict:
    update_data = {}

    if name is not None:
        update_data["name"] = name

    if is_admin is not None:
        update_data["is_admin"] = is_admin

    if regenerate_credentials is not None:
        update_data["regenerate_credentials"] = regenerate_credentials

    response = await authenticated_admin_client.patch(url, json=update_data)
    assert response.status_code == status.HTTP_200_OK

    return response.json()


@pytest.mark.anyio
async def test_update_client(
    authenticated_admin_client: AsyncClient,
) -> None:
    name = "Service D"
    is_admin = False

    data = await create_new_client(
        authenticated_admin_client,
        name=name,
        is_admin=is_admin,
    )
    check_client_data(
        data,
        expected_name=name,
        expected_is_admin=is_admin,
        credentials=True,
    )

    url = API_CLIENT_ID_ENDPOINT.format(id=data["id"])

    # Update name
    new_name = "Updated Service"
    data = await update_client(
        authenticated_admin_client,
        url=url,
        name=new_name,
    )
    check_client_data(data, expected_name=new_name, expected_is_admin=is_admin)

    # Update is_admin
    for is_admin in [True, False]:
        data = await update_client(
            authenticated_admin_client,
            url=url,
            is_admin=is_admin,
        )
        check_client_data(
            data,
            expected_name=new_name,
            expected_is_admin=is_admin,
        )

    # Update credentials
    data = await update_client(
        authenticated_admin_client,
        url=url,
        regenerate_credentials=True,
    )
    check_client_data(
        data,
        expected_name=new_name,
        expected_is_admin=is_admin,
        credentials=True,
    )


@pytest.mark.anyio
async def test_delete_client(
    authenticated_admin_client: AsyncClient,
) -> None:
    clients_to_delete = []

    for name, is_admin in [
        ("Admin Service to Delete", True),
        ("Service to Delete", False),
    ]:
        response = await create_new_client(
            authenticated_admin_client,
            name=name,
            is_admin=is_admin,
        )
        clients_to_delete.append(response)

    for client in clients_to_delete:
        url = API_CLIENT_ID_ENDPOINT.format(id=client["id"])

        response = await authenticated_admin_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = await authenticated_admin_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = await authenticated_admin_client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = await authenticated_admin_client.delete(
        API_CLIENT_ID_ENDPOINT.format(id=9999)
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
