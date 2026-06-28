import os
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
GIS_API_DIR = APP_DIR.parent
REPO_ROOT = GIS_API_DIR.parent

for env_file in (GIS_API_DIR / ".env", APP_DIR / ".env", REPO_ROOT / ".env"):
    if env_file.exists():
        load_dotenv(env_file)
        break
else:
    load_dotenv()


def get_mongo_uri() -> str:
    uri = os.getenv("MongoDB_URI")
    if not uri:
        raise RuntimeError("MongoDB_URI must be set in .env")
    return uri


def get_db_name() -> str:
    db_name = os.getenv("Target_DB_Name") or os.getenv("Source_DB_Name")
    if not db_name:
        raise RuntimeError("Target_DB_Name or Source_DB_Name must be set in .env")
    return db_name


def get_collection_name() -> str:
    return os.getenv("Target_Collection_Name", "ccc_place_names")


def get_poi_collection_name() -> str:
    return os.getenv("Demo_Collection_Name", "demo_place_names")
