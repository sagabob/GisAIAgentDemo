import pytest
from pydantic import ValidationError

from app.queries import build_filters
from app.schemas.common import Geometry


def test_geometry_validates_lng_lat():
    geometry = Geometry(type="Point", coordinates=[172.636, -43.532])
    assert geometry.coordinates == [172.636, -43.532]


def test_geometry_rejects_invalid_longitude():
    with pytest.raises(ValidationError):
        Geometry(type="Point", coordinates=[200, -43.532])


def test_geometry_rejects_short_coordinates():
    with pytest.raises(ValidationError):
        Geometry(type="Point", coordinates=[172.0])


def test_partial_name_search_escapes_regex():
    query = build_filters(name="park.+", exact_name=False)
    assert query["placeName"]["$regex"] == "park\\.\\+"
