import pytest


@pytest.mark.asyncio
async def test_health_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_health_v1_ok(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


@pytest.mark.asyncio
async def test_health_database_unavailable(app):
    from unittest.mock import AsyncMock

    from httpx import ASGITransport, AsyncClient

    from app.config import get_settings

    mock_mongo = AsyncMock()
    mock_mongo.admin.command = AsyncMock(side_effect=RuntimeError("db down"))

    app.state.settings = get_settings()
    app.state.mongo_client = mock_mongo

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.get("/health")

    assert response.status_code == 503
