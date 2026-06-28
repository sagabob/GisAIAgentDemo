"""Classify place names and update GIS points with a category field."""

import argparse
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

from category_verifiers import llm_is_configured, verify_with_llm, verify_with_osm

PROJECT_DIR = Path(__file__).resolve().parent
if PROJECT_DIR.name == ".venv":
    PROJECT_DIR = PROJECT_DIR.parent

REPO_ROOT = PROJECT_DIR.parent
ENV_FILE = REPO_ROOT / ".env"
INPUT_FILE = PROJECT_DIR / "Data" / "PlaceNames" / "place_names_points.json"
OUTPUT_FILE = PROJECT_DIR / "Data" / "PlaceNames" / "place_names_categorized.json"
UNCATEGORIZED_FILE = PROJECT_DIR / "Data" / "PlaceNames" / "place_names_uncategorized.json"

# First matching rule wins. More specific patterns should appear earlier.
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("school", [r"\bschool\b", r"\bcollege\b", r"\buniversity\b", r"\bkindergarten\b", r"\bpreschool\b", r"\bintermediate\b"]),
    ("hospital", [r"\bhospital\b", r"\bmedical centre\b", r"\bclinic\b"]),
    ("cemetery", [r"\bcemetery\b"]),
    ("pool", [r"\bswimming pool\b", r"\bpools\b"]),
    ("library", [r"\blibrary\b"]),
    ("stadium", [r"\bstadium\b"]),
    ("beach", [r"\bbeach\b", r"\bcove\b", r"\bspit\b", r"\bforeshore\b"]),
    ("bay", [r"\bbay\b"]),
    ("waterway", [r"\briver\b", r"\bstream\b", r"\bcreek\b", r"\bestuary\b"]),
    ("walkway", [r"\bwalkway\b", r"\btrack\b", r"\btrail\b"]),
    ("club", [r"\bclub\b"]),
    ("community", [r"\bcommunity centre\b", r"\barts & crafts centre\b", r"\barts and crafts centre\b"]),
    ("memorial", [r"\bmemorial\b"]),
    ("drainage", [r"\bdrainage reserve\b"]),
    ("park", [r"\besplanade reserve\b"]),
    ("conservation_reserve", [
        r"\bconservation reserve\b",
        r"\bscenic reserve\b",
        r"\bwildlife reserve\b",
        r"\bconservation park\b",
        r"\bconservation\b",
        r"\breserve\b",
    ]),
    (
        "park",
        [
            r"\bplayground\b",
            r"\bgarden\b",
            r"\bpark\b",
            r"\bdomain\b",
            r"\btennis courts\b",
            r"\brecreation ground\b",
        ],
    ),
    ("residential", [r"\bflats\b", r"\bcourts\b", r"\bvillage green\b"]),
]


def load_env() -> None:
    if not ENV_FILE.exists():
        raise FileNotFoundError(f".env not found at {ENV_FILE}")
    load_dotenv(ENV_FILE)


def load_config() -> tuple[str, str, str]:
    load_env()

    uri = os.getenv("MongoDB_URI")
    db_name = os.getenv("Target_DB_Name")
    collection_name = os.getenv("Target_Collection_Name")

    if not uri or not db_name or not collection_name:
        raise ValueError(
            "Missing required env vars: MongoDB_URI, Target_DB_Name, Target_Collection_Name"
        )

    return uri, db_name, collection_name


def classify_place_name(place_name: str) -> str:
    name = place_name.lower()
    for category, patterns in CATEGORY_RULES:
        for pattern in patterns:
            if re.search(pattern, name):
                return category
    return "other"


def load_points(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Point data not found at {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}")

    return data


def categorize_with_rules(documents: list[dict]) -> list[dict]:
    categorized = []
    for document in documents:
        place_name = document.get("placeName", "")
        categorized.append(
            {
                **document,
                "category": classify_place_name(place_name),
                "categorySource": "rule",
                "categoryVerified": False,
            }
        )
    return categorized


def save_json(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def build_mongo_update(document: dict) -> dict:
    update_fields = {
        "category": document["category"],
        "categorySource": document.get("categorySource", "rule"),
        "categoryVerified": document.get("categoryVerified", False),
    }
    if document.get("categoryPrevious"):
        update_fields["categoryPrevious"] = document["categoryPrevious"]
    if document.get("categoryEvidence"):
        update_fields["categoryEvidence"] = document["categoryEvidence"]
    return update_fields


def update_categories(uri: str, db_name: str, collection_name: str, documents: list[dict]) -> int:
    operations = [
        UpdateOne(
            {"placeNameId": doc["placeNameId"]},
            {"$set": build_mongo_update(doc)},
        )
        for doc in documents
        if "placeNameId" in doc and "category" in doc
    ]

    client = MongoClient(uri)
    try:
        collection = client[db_name][collection_name]
        result = collection.bulk_write(operations, ordered=False)
        return result.modified_count + result.upserted_count
    finally:
        client.close()


def print_summary(documents: list[dict]) -> None:
    category_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}

    for document in documents:
        category = document["category"]
        source = document.get("categorySource", "rule")
        category_counts[category] = category_counts.get(category, 0) + 1
        source_counts[source] = source_counts.get(source, 0) + 1

    print("Category summary:")
    for category, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {category}: {count}")

    print("Category source summary:")
    for source, count in sorted(source_counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {source}: {count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Categorize GIS place names and update MongoDB.")
    parser.add_argument(
        "--mode",
        choices=["rules", "hybrid"],
        default=os.getenv("CATEGORY_MODE", "rules"),
        help="rules = keyword rules only; hybrid = rules, then OSM, then optional LLM for remaining other",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process only the first N documents (useful for testing internet/LLM lookup)",
    )
    parser.add_argument(
        "--llm-scope",
        choices=["other", "all"],
        default=os.getenv("LLM_SCOPE", "all"),
        help="other = LLM only for uncategorized; all = LLM confirms every category",
    )
    parser.add_argument(
        "--skip-osm",
        action="store_true",
        help="Skip OpenStreetMap verification",
    )
    parser.add_argument(
        "--skip-mongodb",
        action="store_true",
        help="Do not update MongoDB",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    uri, db_name, collection_name = load_config()
    documents = load_points(INPUT_FILE)

    if args.limit > 0:
        documents = documents[: args.limit]

    categorized = categorize_with_rules(documents)
    other_before = sum(1 for doc in categorized if doc["category"] == "other")
    print(f"Loaded {len(documents)} documents from {INPUT_FILE}")
    print(f"Rule-based categorization complete. Remaining other: {other_before}")

    if args.mode == "hybrid":
        use_osm = not args.skip_osm and os.getenv("USE_OSM_VERIFICATION", "true").lower() == "true"
        use_llm = os.getenv("USE_LLM_VERIFICATION", "true").lower() == "true"
        llm_scope_all = args.llm_scope == "all"

        if use_osm and not llm_scope_all:
            radius = int(os.getenv("OSM_LOOKUP_RADIUS_METERS", "120"))
            delay = float(os.getenv("OSM_REQUEST_DELAY_SECONDS", "1.1"))
            print(f"Verifying remaining 'other' records with OpenStreetMap (radius={radius}m)...")
            categorized = verify_with_osm(
                categorized,
                radius_meters=radius,
                delay_seconds=delay,
                only_other=True,
            )
            other_after_osm = sum(1 for doc in categorized if doc["category"] == "other")
            print(f"After OSM verification. Remaining other: {other_after_osm}")

        if use_llm:
            if llm_is_configured():
                scope_label = "all records" if llm_scope_all else "remaining 'other' records"
                print(f"Confirming categories with LLM for {scope_label}...")

                def report_progress(completed: int, total: int) -> None:
                    print(f"  LLM progress: {completed}/{total}")

                categorized = verify_with_llm(
                    categorized,
                    only_other=not llm_scope_all,
                    confirm=llm_scope_all,
                    on_batch_complete=report_progress,
                )
                other_after_llm = sum(1 for doc in categorized if doc["category"] == "other")
                changed = sum(1 for doc in categorized if doc.get("categoryPrevious"))
                print(f"After LLM verification. Remaining other: {other_after_llm}")
                if llm_scope_all:
                    print(f"LLM changed {changed} categories from the rule-based suggestion.")
            else:
                print("LLM verification skipped. Set OPENAI_API_KEY or Azure OpenAI env vars to enable.")

    save_json(OUTPUT_FILE, categorized)
    uncategorized = [doc for doc in categorized if doc["category"] == "other"]
    save_json(UNCATEGORIZED_FILE, uncategorized)

    print_summary(categorized)
    print(f"Saved categorized JSON: {OUTPUT_FILE}")
    print(f"Saved uncategorized review list ({len(uncategorized)}): {UNCATEGORIZED_FILE}")

    if not args.skip_mongodb:
        print(f"Updating categories in {db_name}.{collection_name}...")
        updated = update_categories(uri, db_name, collection_name, categorized)
        print(f"Updated {updated} documents in MongoDB.")


if __name__ == "__main__":
    main()
