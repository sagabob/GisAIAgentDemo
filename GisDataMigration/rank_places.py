"""Fetch place rankings from Google Places API (New) and update MongoDB."""

import argparse
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

PROJECT_DIR = Path(__file__).resolve().parent
if PROJECT_DIR.name == ".venv":
    PROJECT_DIR = PROJECT_DIR.parent

REPO_ROOT = PROJECT_DIR.parent
ENV_FILE = REPO_ROOT / ".env"
CATEGORIZED_FILE = PROJECT_DIR / "Data" / "PlaceNames" / "place_names_categorized.json"
POINTS_FILE = PROJECT_DIR / "Data" / "PlaceNames" / "place_names_points.json"
OUTPUT_FILE = PROJECT_DIR / "Data" / "PlaceNames" / "place_names_ranked.json"
NOT_FOUND_FILE = PROJECT_DIR / "Data" / "PlaceNames" / "place_names_not_ranked.json"

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = (
    "places.displayName,places.rating,places.userRatingCount,"
    "places.googleMapsUri,places.location,places.primaryType"
)


def load_env() -> None:
    if not ENV_FILE.exists():
        raise FileNotFoundError(f".env not found at {ENV_FILE}")
    load_dotenv(ENV_FILE)


def load_config() -> tuple[str, str, str, str]:
    load_env()

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    uri = os.getenv("MongoDB_URI")
    db_name = os.getenv("Target_DB_Name")
    collection_name = os.getenv("Target_Collection_Name")

    if not api_key:
        raise ValueError("Missing required env var: GOOGLE_MAPS_API_KEY")
    if not uri or not db_name or not collection_name:
        raise ValueError(
            "Missing required env vars: MongoDB_URI, Target_DB_Name, Target_Collection_Name"
        )

    return api_key, uri, db_name, collection_name


def load_places(path_preferred: Path, path_fallback: Path) -> list[dict]:
    path = path_preferred if path_preferred.exists() else path_fallback
    if not path.exists():
        raise FileNotFoundError(f"Place data not found at {path_preferred} or {path_fallback}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}")

    print(f"Loaded places from {path}")
    return data


def normalize_name(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def name_similarity(left: str, right: str) -> float:
    left_norm = normalize_name(left)
    right_norm = normalize_name(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm or left_norm in right_norm or right_norm in left_norm:
        return 1.0

    left_words = set(left_norm.split())
    right_words = set(right_norm.split())
    overlap = left_words & right_words
    if not overlap:
        return 0.0
    return len(overlap) / max(len(left_words), 1)


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def search_place_ranking(
    api_key: str,
    place_name: str,
    locality: str,
    lat: float,
    lon: float,
    search_radius: int,
) -> dict:
    text_query = f"{place_name} {locality} Christchurch New Zealand"
    body = json.dumps(
        {
            "textQuery": text_query,
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": float(search_radius),
                }
            },
            "maxResultCount": 5,
        }
    ).encode()

    request = urllib.request.Request(
        PLACES_TEXT_SEARCH_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": FIELD_MASK,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as error:
        details = error.read().decode()
        if error.code == 429:
            raise RuntimeError("Google Places API rate limit reached. Increase delay and retry.") from error
        raise RuntimeError(f"Google Places API error {error.code}: {details}") from error

    places = payload.get("places", [])
    if not places:
        return {"source": "not_found", "rating": None, "reviewCount": None}

    best_match = None
    best_score = -1.0

    for place in places:
        location = place.get("location") or {}
        result_lat = location.get("latitude")
        result_lon = location.get("longitude")
        if result_lat is None or result_lon is None:
            continue

        distance = haversine_meters(lat, lon, result_lat, result_lon)
        display_name = (place.get("displayName") or {}).get("text", "")
        similarity = name_similarity(place_name, display_name)
        score = similarity - (distance / max(search_radius, 1))

        if distance <= search_radius and similarity >= 0.34 and score > best_score:
            best_score = score
            best_match = {
                "source": "google",
                "rating": place.get("rating"),
                "reviewCount": place.get("userRatingCount"),
                "mapsUrl": place.get("googleMapsUri"),
                "matchedName": display_name,
                "primaryType": place.get("primaryType"),
                "distanceMeters": round(distance, 1),
                "nameSimilarity": round(similarity, 2),
            }

    if best_match:
        return best_match

    return {"source": "not_found", "rating": None, "reviewCount": None}


def rank_documents(
    documents: list[dict],
    api_key: str,
    *,
    search_radius: int,
    delay_seconds: float,
) -> list[dict]:
    ranked = []

    for index, document in enumerate(documents, start=1):
        place_name = document.get("placeName", "")
        locality = document.get("locality", "")
        geometry = document.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []

        if len(coordinates) < 2:
            ranked.append({**document, "ranking": {"source": "not_found", "rating": None, "reviewCount": None}})
            continue

        lon, lat = coordinates[0], coordinates[1]
        ranking = search_place_ranking(
            api_key,
            place_name,
            locality,
            lat,
            lon,
            search_radius,
        )
        ranked.append({**document, "ranking": ranking})

        if index % 10 == 0 or index == len(documents):
            found = sum(1 for doc in ranked if doc.get("ranking", {}).get("source") == "google")
            print(f"  Progress: {index}/{len(documents)} processed, {found} ranked")

        if index < len(documents):
            time.sleep(delay_seconds)

    return ranked


def save_json(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def update_rankings(uri: str, db_name: str, collection_name: str, documents: list[dict]) -> int:
    operations = [
        UpdateOne({"placeNameId": doc["placeNameId"]}, {"$set": {"ranking": doc["ranking"]}})
        for doc in documents
        if "placeNameId" in doc and "ranking" in doc
    ]

    client = MongoClient(uri)
    try:
        collection = client[db_name][collection_name]
        result = collection.bulk_write(operations, ordered=False)
        return result.modified_count + result.upserted_count
    finally:
        client.close()


def print_summary(documents: list[dict]) -> None:
    found = [doc for doc in documents if doc.get("ranking", {}).get("source") == "google"]
    not_found = len(documents) - len(found)
    ratings = [doc["ranking"]["rating"] for doc in found if doc["ranking"].get("rating") is not None]

    print(f"Ranked from Google: {len(found)}")
    print(f"Not found: {not_found}")
    if ratings:
        print(f"Average rating: {sum(ratings) / len(ratings):.2f}")
        print(f"Highest rating: {max(ratings)}")
        top = sorted(
            [doc for doc in found if doc["ranking"].get("rating") is not None],
            key=lambda doc: doc["ranking"]["rating"],
            reverse=True,
        )[:5]
        print("Top rated samples:")
        for doc in top:
            ranking = doc["ranking"]
            print(
                f"  {doc['placeName']} -> {ranking.get('rating')} "
                f"({ranking.get('reviewCount')} reviews)"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Google Places rankings for GIS place names.")
    parser.add_argument("--limit", type=int, default=0, help="Process only the first N places")
    parser.add_argument("--skip-mongodb", action="store_true", help="Do not update MongoDB")
    parser.add_argument(
        "--search-radius",
        type=int,
        default=int(os.getenv("GOOGLE_PLACES_SEARCH_RADIUS_METERS", "500")),
        help="Search radius in meters for matching results",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=float(os.getenv("GOOGLE_PLACES_REQUEST_DELAY_SECONDS", "0.2")),
        help="Delay between API requests in seconds",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key, uri, db_name, collection_name = load_config()
    documents = load_places(CATEGORIZED_FILE, POINTS_FILE)

    if args.limit > 0:
        documents = documents[: args.limit]

    print(f"Fetching rankings for {len(documents)} places...")
    ranked = rank_documents(
        documents,
        api_key,
        search_radius=args.search_radius,
        delay_seconds=args.delay,
    )

    not_ranked = [doc for doc in ranked if doc.get("ranking", {}).get("source") != "google"]
    save_json(OUTPUT_FILE, ranked)
    save_json(NOT_FOUND_FILE, not_ranked)

    print_summary(ranked)
    print(f"Saved ranked JSON: {OUTPUT_FILE}")
    print(f"Saved not ranked list ({len(not_ranked)}): {NOT_FOUND_FILE}")

    if not args.skip_mongodb:
        print(f"Updating rankings in {db_name}.{collection_name}...")
        updated = update_rankings(uri, db_name, collection_name, ranked)
        print(f"Updated {updated} documents in MongoDB.")


if __name__ == "__main__":
    main()
