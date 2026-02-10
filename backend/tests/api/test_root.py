import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_root(async_client: AsyncClient) -> None:
    # Async test example
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
