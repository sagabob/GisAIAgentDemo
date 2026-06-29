from unittest.mock import AsyncMock

import pytest

from app.dependencies import get_place_repository
from app.schemas.common import Geometry
from app.schemas.place import Place, PlaceListResponse


@pytest.mark.asyncio
async def test_search_places(client, app):
    mock_repo = AsyncMock()
    mock_repo.search.return_value = PlaceListResponse(
        total=1,
        skip=0,
        limit=20,
        sortBy="name",
        sortOrder="asc",
        items=[
            Place(
                placeNameId=1,
                placeName="Test Park",
                geometry=Geometry(type="Point", coordinates=[172.63, -43.53]),
            )
        ],
    )
    app.dependency_overrides[get_place_repository] = lambda: mock_repo

    response = await client.get("/places", params={"name": "park", "limit": 10})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["placeName"] == "Test Park"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_place_not_found(client, app):
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None
    app.dependency_overrides[get_place_repository] = lambda: mock_repo

    response = await client.get("/places/999")
    assert response.status_code == 404

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_v1_search_places(client, app):
    mock_repo = AsyncMock()
    mock_repo.search.return_value = PlaceListResponse(
        total=0,
        skip=0,
        limit=20,
        sortBy="name",
        sortOrder="asc",
        items=[],
    )
    app.dependency_overrides[get_place_repository] = lambda: mock_repo

    response = await client.get("/api/v1/places", params={"category": "beach"})
    assert response.status_code == 200
    assert response.json()["total"] == 0

    app.dependency_overrides.clear()
