from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AGENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = AGENT_DIR.parent


def _load_env_files() -> None:
    for env_file in (AGENT_DIR / ".env", REPO_ROOT / ".env"):
        if env_file.exists():
            load_dotenv(env_file)
            return
    load_dotenv()


_load_env_files()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore", populate_by_name=True)

    openai_api_key: str = Field(validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    gis_api_base_url: str = Field(validation_alias="GIS_API_BASE_URL")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    max_tool_rounds: int = Field(default=5, validation_alias="MAX_TOOL_ROUNDS")

    @field_validator("openai_api_key")
    @classmethod
    def openai_api_key_required(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("OPENAI_API_KEY must be set")
        return value.strip()

    @field_validator("gis_api_base_url")
    @classmethod
    def gis_api_base_url_required(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("GIS_API_BASE_URL must be set in .env")
        return value.strip().rstrip("/")


    @property
    def gis_api_url(self) -> str:
        return self.gis_api_base_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_openai_api_key() -> str:
    return get_settings().openai_api_key


def get_openai_model() -> str:
    return get_settings().openai_model


def get_gis_api_base_url() -> str:
    return get_settings().gis_api_url
