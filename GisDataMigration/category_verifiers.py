"""Internet and LLM helpers to verify or assign place name categories."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Callable

USER_AGENT = "GisAIAgentDemo/1.0 (gis-data-migration; contact=local-dev)"

VALID_CATEGORIES = {
    "school",
    "hospital",
    "cemetery",
    "pool",
    "library",
    "stadium",
    "beach",
    "bay",
    "waterway",
    "walkway",
    "club",
    "community",
    "memorial",
    "drainage",
    "conservation_reserve",
    "park",
    "residential",
    "other",
}


def _fetch_json(url: str, data: bytes | None = None) -> dict | list:
    request = urllib.request.Request(
        url,
        data=data,
        method="POST" if data else "GET",
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded" if data else "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read())


def _tag_value(tags: dict[str, str], key: str) -> str:
    return tags.get(key, "").lower()


def category_from_osm_tags(tags: dict[str, str]) -> str | None:
    amenity = _tag_value(tags, "amenity")
    leisure = _tag_value(tags, "leisure")
    natural = _tag_value(tags, "natural")
    landuse = _tag_value(tags, "landuse")
    sport = _tag_value(tags, "sport")
    name = _tag_value(tags, "name")

    if amenity in {"school", "college", "university", "kindergarten"}:
        return "school"
    if amenity in {"hospital", "clinic"}:
        return "hospital"
    if amenity in {"grave_yard", "funeral_hall"} or landuse == "cemetery":
        return "cemetery"
    if amenity == "library":
        return "library"
    if amenity in {"community_centre", "social_centre", "arts_centre"}:
        return "community"
    if amenity in {"swimming_pool", "public_bath"}:
        return "pool"
    if amenity == "stadium" or leisure == "stadium":
        return "stadium"

    if leisure == "nature_reserve" or landuse == "conservation":
        return "conservation_reserve"
    if leisure in {"park", "playground", "garden", "recreation_ground"}:
        if "reserve" in name and "drainage" not in name:
            return "conservation_reserve"
        return "park"
    if leisure in {"sports_centre", "fitness_centre"}:
        return "club"
    if leisure == "pitch" and sport in {"tennis", "golf", "bowls", "cricket", "rugby"}:
        return "club"

    if natural in {"beach", "coastline", "sand"}:
        return "beach"
    if natural in {"bay", "cape"}:
        return "bay"
    if natural in {"water", "wetland"}:
        return "waterway"
    if _tag_value(tags, "waterway"):
        return "waterway"

    if landuse in {"residential", "allotments"}:
        return "residential"

    return None


def lookup_category_from_osm(
    lat: float,
    lon: float,
    radius_meters: int = 120,
) -> tuple[str | None, dict[str, Any]]:
    query = f"""
    [out:json][timeout:25];
    (
      node(around:{radius_meters},{lat},{lon})[leisure];
      node(around:{radius_meters},{lat},{lon})[amenity];
      node(around:{radius_meters},{lat},{lon})[natural];
      node(around:{radius_meters},{lat},{lon})[landuse];
      way(around:{radius_meters},{lat},{lon})[leisure];
      way(around:{radius_meters},{lat},{lon})[amenity];
      way(around:{radius_meters},{lat},{lon})[natural];
      way(around:{radius_meters},{lat},{lon})[landuse];
    );
    out tags center;
    """
    try:
        payload = _fetch_json("https://overpass-api.de/api/interpreter", query.encode())
    except urllib.error.HTTPError as error:
        return None, {"error": f"overpass HTTP {error.code}"}

    elements = payload.get("elements", []) if isinstance(payload, dict) else []
    matched_tags: list[dict[str, str]] = []

    for element in elements:
        tags = element.get("tags") or {}
        category = category_from_osm_tags(tags)
        if category:
            return category, {"matchedTags": tags, "source": "osm"}

        if tags:
            matched_tags.append(tags)

    return None, {"nearbyTags": matched_tags[:5], "source": "osm"}


def _openai_chat(messages: list[dict[str, str]]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    body = json.dumps({"model": model, "messages": messages, "temperature": 0}).encode()
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as error:
        details = error.read().decode()
        if error.code == 429 and "insufficient_quota" in details:
            raise RuntimeError(
                "OpenAI quota exceeded. Add billing credits at https://platform.openai.com/settings/organization/billing"
            ) from error
        raise RuntimeError(f"OpenAI API error {error.code}: {details}") from error
    return payload["choices"][0]["message"]["content"]


def _azure_openai_chat(messages: list[dict[str, str]]) -> str:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

    if not endpoint or not api_key or not deployment:
        raise RuntimeError("Azure OpenAI env vars are not fully configured")

    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    body = json.dumps({"messages": messages, "temperature": 0}).encode()
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read())
    return payload["choices"][0]["message"]["content"]


def _chat_completion(messages: list[dict[str, str]]) -> str:
    if os.getenv("AZURE_OPENAI_ENDPOINT"):
        return _azure_openai_chat(messages)
    return _openai_chat(messages)


def _extract_json_array(content: str) -> list[dict[str, Any]]:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```", 2)[1]
        if content.startswith("json"):
            content = content[4:]
    data = json.loads(content.strip())
    if not isinstance(data, list):
        raise ValueError("LLM response was not a JSON array")
    return data


def classify_places_with_llm(documents: list[dict], *, confirm: bool = False) -> dict[int, str]:
    if not documents:
        return {}

    category_list = ", ".join(sorted(VALID_CATEGORIES))
    lines = []
    for doc in documents:
        if "placeNameId" not in doc:
            continue
        locality = doc.get("locality", "unknown")
        if confirm:
            suggested = doc.get("category", "other")
            lines.append(
                f'- placeNameId {doc["placeNameId"]}: "{doc["placeName"]}" in {locality} (suggested: {suggested})'
            )
        else:
            lines.append(f'- placeNameId {doc["placeNameId"]}: "{doc["placeName"]}" in {locality}')

    confirm_instruction = (
        "Confirm or correct each suggested category. Keep the suggestion when it is already correct."
        if confirm
        else "Classify each place name."
    )
    prompt = f"""{confirm_instruction}
Each place must use exactly one category from this list: {category_list}

Rules:
- Use conservation_reserve for protected reserves and scenic/nature reserves.
- Use park for public parks and playgrounds.
- Use club for sports clubs and tennis/bowls/golf clubs.
- Use residential for housing complexes, flats, and courts.
- Use other only when nothing else fits.

Return ONLY a JSON array like:
[{{"placeNameId": 123, "category": "park"}}]

Places:
{chr(10).join(lines)}
"""

    content = _chat_completion(
        [
            {"role": "system", "content": "You classify New Zealand place names. Return valid JSON only."},
            {"role": "user", "content": prompt},
        ]
    )
    results = _extract_json_array(content)

    mapping: dict[int, str] = {}
    for item in results:
        place_name_id = item.get("placeNameId")
        category = str(item.get("category", "other")).lower()
        if place_name_id is not None and category in VALID_CATEGORIES:
            mapping[int(place_name_id)] = category
    return mapping


def llm_is_configured() -> bool:
    if os.getenv("OPENAI_API_KEY"):
        return True
    return bool(
        os.getenv("AZURE_OPENAI_ENDPOINT")
        and os.getenv("AZURE_OPENAI_API_KEY")
        and os.getenv("AZURE_OPENAI_DEPLOYMENT")
    )


def verify_with_osm(
    documents: list[dict],
    *,
    radius_meters: int,
    delay_seconds: float,
    only_other: bool = True,
) -> list[dict]:
    verified: list[dict] = []
    for index, document in enumerate(documents, start=1):
        current_category = document.get("category", "other")
        if only_other and current_category != "other":
            verified.append(document)
            continue

        geometry = document.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        if len(coordinates) < 2:
            verified.append(document)
            continue

        lon, lat = coordinates[0], coordinates[1]
        osm_category, evidence = lookup_category_from_osm(lat, lon, radius_meters)

        updated = {**document}
        if osm_category:
            updated["category"] = osm_category
            updated["categorySource"] = "osm"
            updated["categoryVerified"] = True
            updated["categoryEvidence"] = evidence
        else:
            updated["categorySource"] = document.get("categorySource", "rule")
            updated["categoryVerified"] = False
            updated["categoryEvidence"] = evidence

        verified.append(updated)

        if index < len(documents):
            time.sleep(delay_seconds)

    return verified


def verify_with_llm(
    documents: list[dict],
    *,
    batch_size: int = 20,
    only_other: bool = True,
    confirm: bool = False,
    on_batch_complete: Callable[[int, int], None] | None = None,
) -> list[dict]:
    if not llm_is_configured():
        raise RuntimeError("LLM verification requested but no OpenAI/Azure OpenAI credentials are configured")

    targets = [
        doc
        for doc in documents
        if (not only_other or doc.get("category") == "other")
    ]
    llm_results: dict[int, str] = {}

    for start in range(0, len(targets), batch_size):
        batch = targets[start : start + batch_size]
        llm_results.update(classify_places_with_llm(batch, confirm=confirm))
        if on_batch_complete:
            on_batch_complete(min(start + batch_size, len(targets)), len(targets))
        if start + batch_size < len(targets):
            time.sleep(0.5)

    verified: list[dict] = []
    for document in documents:
        place_name_id = document.get("placeNameId")
        if place_name_id in llm_results:
            previous_category = document.get("category")
            final_category = llm_results[place_name_id]
            updated = {
                **document,
                "category": final_category,
                "categorySource": "llm",
                "categoryVerified": True,
            }
            if confirm and previous_category and previous_category != final_category:
                updated["categoryPrevious"] = previous_category
            verified.append(updated)
        else:
            verified.append(document)

    return verified
