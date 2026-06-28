import re
from typing import Any

from app.enums import SortBy, SortOrder
from app.models import Place


def build_filters(
    *,
    name: str | None = None,
    category: str | None = None,
    locality: str | None = None,
    exact_name: bool = False,
) -> dict[str, Any]:
    query: dict[str, Any] = {}

    if name:
        if exact_name:
            query["placeName"] = {"$regex": f"^{re.escape(name)}$", "$options": "i"}
        else:
            query["placeName"] = {"$regex": name, "$options": "i"}
    if category:
        query["category"] = category
    if locality:
        query["locality"] = {"$regex": locality, "$options": "i"}

    return query


def build_sort(sort_by: SortBy, sort_order: SortOrder) -> list[tuple[str, int]]:
    direction = 1 if sort_order == SortOrder.asc else -1

    if sort_by == SortBy.name:
        return [("placeName", direction), ("placeNameId", 1)]

    if sort_order == SortOrder.desc:
        return [("ranking.rating", -1), ("ranking.reviewCount", -1), ("placeName", 1)]

    return [("ranking.rating", 1), ("placeName", 1)]


def build_bounds_geometry(*, north: float, south: float, east: float, west: float) -> dict[str, Any]:
    return {
        "geometry": {
            "$geoWithin": {
                "$geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [west, south],
                            [east, south],
                            [east, north],
                            [west, north],
                            [west, south],
                        ]
                    ],
                }
            }
        }
    }


def merge_query(*parts: dict[str, Any]) -> dict[str, Any]:
    query: dict[str, Any] = {}
    for part in parts:
        query.update(part)
    return query


def serialize_place(document: dict[str, Any]) -> Place:
    payload = {key: value for key, value in document.items() if key != "_id"}
    return Place.model_validate(payload)
