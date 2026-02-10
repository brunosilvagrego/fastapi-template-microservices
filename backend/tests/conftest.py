import pytest
from app.main import app
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client
