"""Export place_names from MongoDB and convert MultiPoint geometry to Point."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

PROJECT_DIR = Path(__file__).resolve().parent
if PROJECT_DIR.name == ".venv":
    PROJECT_DIR = PROJECT_DIR.parent

REPO_ROOT = PROJECT_DIR.parent
ENV_FILE = REPO_ROOT / ".env"
OUTPUT_DIR = PROJECT_DIR / "Data/PlaceNames"


def load_config() -> tuple[str, str, str]:
    if not ENV_FILE.exists():
        raise FileNotFoundError(f".env not found at {ENV_FILE}")

    load_dotenv(ENV_FILE)

    uri = os.getenv("MongoDB_URI")
    db_name = os.getenv("Source_DB_Name")
    collection_name = os.getenv("Source_Collection_Name")

    if not uri or not db_name or not collection_name:
        raise ValueError(
            "Missing required env vars: MongoDB_URI, Source_DB_Name, Source_Collection_Name"
        )

    return uri, db_name, collection_name


def multipoint_to_point(geometry: dict | None) -> dict | None:
    if not geometry:
        return geometry

    if geometry.get("type") != "MultiPoint":
        return geometry

    coordinates = geometry.get("coordinates") or []
    if not coordinates:
        return {"type": "Point", "coordinates": []}

    return {"type": "Point", "coordinates": coordinates[0]}


def document_without_id(doc: dict) -> dict:
    return {key: value for key, value in doc.items() if key != "_id"}


def convert_document(doc: dict) -> dict:
    converted = document_without_id(doc)
    if "geometry" in converted:
        converted["geometry"] = multipoint_to_point(converted["geometry"])
    return converted


def fetch_documents(uri: str, db_name: str, collection_name: str) -> list[dict]:
    client = MongoClient(uri)
    try:
        collection = client[db_name][collection_name]
        return list(collection.find({}))
    finally:
        client.close()


def save_json(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def main() -> None:
    uri, db_name, collection_name = load_config()

    print(f"Fetching documents from {db_name}.{collection_name}...")
    documents = fetch_documents(uri, db_name, collection_name)
    print(f"Fetched {len(documents)} documents.")

    raw_output = [document_without_id(doc) for doc in documents]
    points_output = [convert_document(doc) for doc in documents]

    raw_path = OUTPUT_DIR / "place_names_raw.json"
    points_path = OUTPUT_DIR / "place_names_points.json"

    save_json(raw_path, raw_output)
    save_json(points_path, points_output)

    print(f"Saved raw JSON (no _id): {raw_path}")
    print(f"Saved Point JSON (no _id): {points_path}")


if __name__ == "__main__":
    main()
