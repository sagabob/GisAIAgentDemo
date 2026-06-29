from unittest.mock import AsyncMock, MagicMock

import pytest
from pymongo.errors import DuplicateKeyError

from app.repositories.pointofinterest import PointOfInterestRepository
from app.schemas.common import Geometry
from app.schemas.poi import PointOfInterestCreate


@pytest.mark.asyncio
async def test_create_retries_on_duplicate_key():
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=None)
    collection.insert_one = AsyncMock(
        side_effect=[DuplicateKeyError("dup"), DuplicateKeyError("dup"), DuplicateKeyError("dup")]
    )

    repository = PointOfInterestRepository(collection)
    payload = PointOfInterestCreate(
        placeName="Retry Park",
        geometry=Geometry(type="Point", coordinates=[172.63, -43.53]),
    )

    with pytest.raises(ValueError, match="unique placeNameId"):
        await repository.create(payload)

    assert collection.insert_one.await_count == 3
