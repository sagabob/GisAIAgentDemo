from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parent
GIS_API_DIR = APP_DIR.parent
REPO_ROOT = GIS_API_DIR.parent


def _load_env_files() -> None:
    for env_file in (GIS_API_DIR / ".env", APP_DIR / ".env", REPO_ROOT / ".env"):
        if env_file.exists():
            load_dotenv(env_file)
            return
    load_dotenv()


_load_env_files()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        populate_by_name=True,
    )

    mongodb_uri: str = Field(validation_alias="MongoDB_URI")
    target_db_name: str | None = Field(default=None, validation_alias="Target_DB_Name")
    source_db_name: str | None = Field(default=None, validation_alias="Source_DB_Name")
    target_collection_name: str = Field(default="ccc_place_names", validation_alias="Target_Collection_Name")
    demo_collection_name: str = Field(default="demo_place_names", validation_alias="Demo_Collection_Name")
    cors_origins: str = Field(default="*", validation_alias="CORS_ORIGINS")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @property
    def db_name(self) -> str:
        name = self.target_db_name or self.source_db_name
        if not name:
            raise ValueError("Target_DB_Name or Source_DB_Name must be set")
        return name

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("mongodb_uri")
    @classmethod
    def mongodb_uri_required(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("MongoDB_URI must be set")
        return value.strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
