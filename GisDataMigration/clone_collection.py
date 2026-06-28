"""Clone a MongoDB collection within the same database."""

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


def load_env() -> None:
    if not ENV_FILE.exists():
        raise FileNotFoundError(f".env not found at {ENV_FILE}")
    load_dotenv(ENV_FILE)


def clone_collection(
    uri: str,
    db_name: str,
    source_collection: str,
    target_collection: str,
    *,
    mode: str,
    merge_key: str | None,
    exclude_id: bool,
    drop_target: bool,
) -> tuple[int, int]:
    client = MongoClient(uri)
    try:
        db = client[db_name]
        source = db[source_collection]
        target = db[target_collection]

        source_count = source.count_documents({})

        if source_collection == target_collection:
            raise ValueError("Source and target collection names must be different.")

        if drop_target and target_collection in db.list_collection_names():
            target.drop()
            print(f"Dropped existing collection {db_name}.{target_collection}")

        pipeline: list[dict] = [{"$match": {}}]

        if exclude_id:
            pipeline.append({"$project": {"_id": 0}})

        if mode == "out":
            pipeline.append({"$out": target_collection})
            source.aggregate(pipeline)
        elif mode == "merge":
            if not merge_key:
                raise ValueError("merge mode requires --merge-key")
            pipeline.append(
                {
                    "$merge": {
                        "into": target_collection,
                        "on": merge_key,
                        "whenMatched": "replace",
                        "whenNotMatched": "insert",
                    }
                }
            )
            source.aggregate(pipeline)
        else:
            raise ValueError(f"Unsupported mode: {mode}")

        target_count = target.count_documents({})
        return source_count, target_count
    finally:
        client.close()


def parse_args() -> argparse.Namespace:
    load_env()

    parser = argparse.ArgumentParser(description="Clone a MongoDB collection.")
    parser.add_argument(
        "--db",
        default=os.getenv("Target_DB_Name") or os.getenv("Source_DB_Name"),
        help="Database name (default: Target_DB_Name or Source_DB_Name from .env)",
    )
    parser.add_argument(
        "--source",
        default=os.getenv("Source_Collection_Name"),
        help="Source collection name (default: Source_Collection_Name from .env)",
    )
    parser.add_argument(
        "--target",
        default=os.getenv("Target_Collection_Name"),
        help="Target collection name (default: Target_Collection_Name from .env)",
    )
    parser.add_argument(
        "--mode",
        choices=["out", "merge"],
        default="out",
        help="Clone mode: out replaces target collection, merge upserts by key",
    )
    parser.add_argument(
        "--merge-key",
        default="placeNameId",
        help="Field used for merge mode (default: placeNameId)",
    )
    parser.add_argument(
        "--exclude-id",
        action="store_true",
        help="Exclude MongoDB _id from cloned documents",
    )
    parser.add_argument(
        "--drop-target",
        action="store_true",
        help="Drop target collection before cloning",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    uri = os.getenv("MongoDB_URI")

    if not uri:
        raise ValueError("Missing required env var: MongoDB_URI")
    if not args.db or not args.source or not args.target:
        raise ValueError("Database, source collection, and target collection are required.")

    print(
        f"Cloning {args.db}.{args.source} -> {args.db}.{args.target} "
        f"(mode={args.mode}, exclude_id={args.exclude_id})"
    )

    source_count, target_count = clone_collection(
        uri,
        args.db,
        args.source,
        args.target,
        mode=args.mode,
        merge_key=args.merge_key,
        exclude_id=args.exclude_id,
        drop_target=args.drop_target,
    )

    print(f"Source documents: {source_count}")
    print(f"Target documents: {target_count}")
    print("Clone completed.")


if __name__ == "__main__":
    main()
