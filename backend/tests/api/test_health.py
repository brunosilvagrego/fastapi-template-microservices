from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

API_HEALTH_ENDPOINT = "/api/health"


def test_health_status(client: TestClient) -> None:
    """Test running database."""
    response = client.get(API_HEALTH_ENDPOINT)
    assert response.status_code == 204


@pytest.mark.parametrize(
    "db_health,expected_status",
    [
        (False, 503),
        (True, 204),
    ],
)
@patch("app.api.health.db_health_check", new_callable=AsyncMock)
def test_health_status_mocked(
    mock_db_health_check: AsyncMock,
    client: TestClient,
    db_health: bool,
    expected_status: int,
) -> None:
    """Test health status with mocked database health check."""
    mock_db_health_check.return_value = db_health
    response = client.get(API_HEALTH_ENDPOINT)
    assert response.status_code == expected_status
