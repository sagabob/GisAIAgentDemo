from typing import Any


def extract_total(result: Any) -> int | None:
    if isinstance(result, dict) and isinstance(result.get("total"), int):
        return result["total"]
    return None


def build_places_answer(places: list[dict[str, Any]], total: int | None) -> str:
    shown = len(places)
    count = total or shown
    if shown < count:
        return f"Found {count} places. Showing {shown} - select one to view on the map."
    if shown == 1:
        return "Found 1 place. Select it below to view on the map."
    return f"Found {shown} places. Select one below to view on the map."


def extract_places(result: Any) -> list[dict[str, Any]]:
    if not isinstance(result, dict):
        return []

    if isinstance(result.get("items"), list):
        return [item for item in result["items"] if isinstance(item, dict) and item.get("geometry")]

    if result.get("geometry"):
        return [result]

    return []


def dedupe_places(places: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[int] = set()
    unique: list[dict[str, Any]] = []
    for place in places:
        place_id = place.get("placeNameId")
        if place_id is None or place_id in seen:
            continue
        seen.add(place_id)
        unique.append(place)
    return unique
