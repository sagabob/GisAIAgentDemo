import pytest

from places import build_places_answer, dedupe_places, extract_places, extract_total


def test_extract_places_from_list():
    result = {"total": 2, "items": [{"placeNameId": 1, "geometry": {"type": "Point", "coordinates": [1, 2]}}]}
    places = extract_places(result)
    assert len(places) == 1
    assert places[0]["placeNameId"] == 1


def test_extract_places_skips_items_without_geometry():
    result = {"items": [{"placeNameId": 1}, {"placeNameId": 2, "geometry": {}}]}
    assert extract_places(result) == []


def test_dedupe_places():
    places = [{"placeNameId": 1}, {"placeNameId": 1}, {"placeNameId": 2}]
    assert len(dedupe_places(places)) == 2


def test_build_places_answer_truncated():
    text = build_places_answer([{}] * 20, 50)
    assert "Found 50 places" in text
    assert "Showing 20" in text


def test_extract_total():
    assert extract_total({"total": 10}) == 10
    assert extract_total({"total": "10"}) is None
