from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        extra="allow",
    )

    TARGET_ENV: str = Field(default="local-dev")

    DB_NAME: str = Field(default="trading_bot", alias="POSTGRES_DB")
    DB_USER: str = Field(default="postgres", alias="POSTGRES_USER")
    DB_PASSWORD: str = Field(default="postgres", alias="POSTGRES_PASSWORD")

    DB_HOST: str = Field(default="0.0.0.0", alias="POSTGRES_HOST")
    DB_PORT: int = Field(default=5432, alias="POSTGRES_PORT")

    DB_POOL_SIZE: int = Field(default=4)
    DB_MAX_OVERFLOW: int = Field(default=2)

    BASE_URL: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    NUM_WORKERS: int = Field(default=2)

    API_VERSION: str = Field(default="0.1.0")
    IMAGE_TAG: str = Field(default="local-latest")

    @property
    def db_url(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def async_db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

# Dependency-safe and test-friendly
@lru_cache()
def get_settings() -> Settings:
    return Settings()