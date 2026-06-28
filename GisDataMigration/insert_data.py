"""Insert GIS Point documents from JSON into the target MongoDB collection."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient, ReplaceOne

PROJECT_DIR = Path(__file__).resolve().parent
if PROJECT_DIR.name == ".venv":
    PROJECT_DIR = PROJECT_DIR.parent

REPO_ROOT = PROJECT_DIR.parent
ENV_FILE = REPO_ROOT / ".env"
INPUT_FILE = PROJECT_DIR / "Data" / "PlaceNames" / "place_names_points.json"


def load_config() -> tuple[str, str, str]:
    if not ENV_FILE.exists():
        raise FileNotFoundError(f".env not found at {ENV_FILE}")

    load_dotenv(ENV_FILE)

    uri = os.getenv("MongoDB_URI")
    db_name = os.getenv("Target_DB_Name")
    collection_name = os.getenv("Target_Collection_Name")

    if not uri or not db_name or not collection_name:
        raise ValueError(
            "Missing required env vars: MongoDB_URI, Target_DB_Name, Target_Collection_Name"
        )

    return uri, db_name, collection_name


def load_points(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Point data not found at {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}")

    return data


def insert_points(uri: str, db_name: str, collection_name: str, documents: list[dict]) -> tuple[int, int]:
    operations = [
        ReplaceOne({"placeNameId": doc["placeNameId"]}, doc, upsert=True)
        for doc in documents
        if "placeNameId" in doc
    ]

    if len(operations) != len(documents):
        skipped = len(documents) - len(operations)
        print(f"Skipped {skipped} documents without placeNameId.")

    client = MongoClient(uri)
    try:
        collection = client[db_name][collection_name]
        result = collection.bulk_write(operations, ordered=False)
        inserted = result.upserted_count
        updated = result.modified_count
        return inserted, updated
    finally:
        client.close()


def main() -> None:
    uri, db_name, collection_name = load_config()
    documents = load_points(INPUT_FILE)

    print(f"Loaded {len(documents)} point documents from {INPUT_FILE}")
    print(f"Inserting into {db_name}.{collection_name}...")

    inserted, updated = insert_points(uri, db_name, collection_name, documents)

    print(f"Inserted {inserted} documents.")
    print(f"Updated {updated} existing documents.")


if __name__ == "__main__":
    main()
