"""Remove selected fields from documents in a MongoDB collection."""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

PROJECT_DIR = Path(__file__).resolve().parent
if PROJECT_DIR.name == ".venv":
    PROJECT_DIR = PROJECT_DIR.parent

REPO_ROOT = PROJECT_DIR.parent
ENV_FILE = REPO_ROOT / ".env"

DEFAULT_FIELDS = ("ranking", "categorySource", "categoryVerified")
DEFAULT_COLLECTION = "demo_place_names"


def load_env() -> None:
    if not ENV_FILE.exists():
        raise FileNotFoundError(f".env not found at {ENV_FILE}")
    load_dotenv(ENV_FILE)


def remove_fields(
    uri: str,
    db_name: str,
    collection_name: str,
    fields: list[str],
) -> tuple[int, int]:
    unset_spec = {field: "" for field in fields}
    query = {"$or": [{field: {"$exists": True}} for field in fields]}

    client = MongoClient(uri)
    try:
        collection = client[db_name][collection_name]
        matched = collection.count_documents(query)
        result = collection.update_many(query, {"$unset": unset_spec})
        return matched, result.modified_count
    finally:
        client.close()


def parse_args() -> argparse.Namespace:
    load_env()

    parser = argparse.ArgumentParser(description="Remove fields from MongoDB collection documents.")
    parser.add_argument(
        "--db",
        default=os.getenv("Target_DB_Name") or os.getenv("Source_DB_Name"),
        help="Database name (default: Target_DB_Name or Source_DB_Name from .env)",
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help=f"Collection name (default: {DEFAULT_COLLECTION})",
    )
    parser.add_argument(
        "--fields",
        nargs="+",
        default=list(DEFAULT_FIELDS),
        help="Field names to remove",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    uri = os.getenv("MongoDB_URI")

    if not uri:
        raise ValueError("Missing required env var: MongoDB_URI")
    if not args.db or not args.collection:
        raise ValueError("Database and collection are required.")

    print(f"Removing fields from {args.db}.{args.collection}: {', '.join(args.fields)}")

    matched, modified = remove_fields(uri, args.db, args.collection, args.fields)

    print(f"Documents matched: {matched}")
    print(f"Documents updated: {modified}")
    print("Field removal completed.")


if __name__ == "__main__":
    main()
