import pytest
from app.api.deps import get_db_session
from app.core.config import settings
from app.core.database import SessionManager, engine
from app.main import app
from httpx import ASGITransport, AsyncClient

from .utils import make_authenticated_client


async def get_test_db_session():
    """Test-specific database session that creates a fresh connection each
    time."""
    async with SessionManager() as db_session:
        try:
            yield db_session
        finally:
            await db_session.close()


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for all async tests."""
    return "asyncio"


@pytest.fixture(autouse=True)
async def override_get_db_session():
    """Override the database session dependency for tests."""
    app.dependency_overrides[get_db_session] = get_test_db_session
    yield
    app.dependency_overrides.clear()
    # Clean up any remaining connections
    await engine.dispose()


@pytest.fixture()
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as async_client:
        yield async_client


@pytest.fixture
async def authenticated_admin_client(client: AsyncClient) -> AsyncClient:
    return await make_authenticated_client(
        client=client,
        client_id=settings.ADMIN_CLIENT_ID,
        client_secret=settings.ADMIN_CLIENT_SECRET,
    )


@pytest.fixture
async def authenticated_external_client(client: AsyncClient) -> AsyncClient:
    return await make_authenticated_client(
        client=client,
        client_id=settings.EXTERNAL_CLIENT_ID,
        client_secret=settings.EXTERNAL_CLIENT_SECRET,
    )
