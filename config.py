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
    token_ttl_hours: int
    token_secret: str
    max_concurrency: int = 50
    task_await_time: int = 5
    task_check_interval: float = 0.25

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


class ServiceSettings(BaseSettings):
    gov_url: str
    user_profile_url: str
    user_profile_secret: str
    email_url: str
    s1c_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SERVICE_",
        extra="ignore"
    )


class WebviewSettings(BaseSettings):
    url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="WEBVIEW_",
        extra="ignore"
    )


class EmailSettings(BaseSettings):
    compliance_dpt: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="EMAIL_",
        extra="ignore"
    )


class RBKSettings(BaseSettings):
    username: str
    password: str
    url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="RBK_",
        extra="ignore"
    )


class TarlanSettings(BaseSettings):
    api_url: str
    merchant_id: str
    project_id: str
    secret: str
    redirect_url: str
    callback_url: str
    callback_secret: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TARLAN_",
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
    services: ServiceSettings = ServiceSettings()  # type: ignore
    webview: WebviewSettings = WebviewSettings()  # type: ignore
    email: EmailSettings = EmailSettings()  # type: ignore
    rbk: RBKSettings = RBKSettings()  # type: ignore
    tarlan: TarlanSettings = TarlanSettings()  # type: ignore


settings = MainSettings()
