import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("MongoDB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("Target_DB_Name", "test_db")
    monkeypatch.setenv("Target_Collection_Name", "test_places")
    monkeypatch.setenv("Demo_Collection_Name", "test_poi")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    from unittest.mock import AsyncMock

    mock_mongo = AsyncMock()
    mock_mongo.admin.command = AsyncMock(return_value={"ok": 1})

    app.state.settings = get_settings()
    app.state.mongo_client = mock_mongo

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
