from unittest.mock import MagicMock

import pytest

from schemas import AgentResult


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["gisApi"] == "https://example.test"


@pytest.mark.asyncio
async def test_chat_returns_agent_result(client, app):
    mock_agent = MagicMock()
    mock_agent.ask_with_metadata.return_value = AgentResult(
        answer="Found 1 place. Select it below to view on the map.",
        places=[{"placeNameId": 1, "placeName": "Test Beach", "geometry": {"type": "Point", "coordinates": [172.6, -43.5]}}],
        total=1,
    )
    app.state.session_store.get_or_create = lambda _: mock_agent

    response = await client.post("/chat", json={"message": "list beaches"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["places"][0]["placeName"] == "Test Beach"
    assert "session_id" in body


@pytest.mark.asyncio
async def test_reset_chat(client, app):
    mock_agent = MagicMock()
    app.state.session_store.get_or_create = lambda _: mock_agent

    response = await client.post("/chat/reset", json={"session_id": "abc"})
    assert response.status_code == 200
    assert response.json() == {"status": "reset"}
