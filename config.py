import json
from typing import List

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_allowed_origins() -> List[str]:
    return ["*"]


class AppSettings(BaseSettings):
    port: int
    allowed_origins: List[str] | None = None
    secret_key: str
    requests_timeout: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore"
    )

    @field_validator("allowed_origins", mode="before")  # noqa
    @classmethod
    def parse_app_allowed_origins(cls, value):
        if value is None:
            return ["*"]

        if isinstance(value, str):
            return json.loads(value)

        return value


class DatabaseSettings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 5432
    username: str
    password: str
    database: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="POSTGRES_",
        extra="ignore"
    )


class MainSettings(BaseModel):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore"
    )

    app: AppSettings = AppSettings()  # type: ignore
    database: DatabaseSettings = DatabaseSettings()  # type: ignore


settings = MainSettings()
