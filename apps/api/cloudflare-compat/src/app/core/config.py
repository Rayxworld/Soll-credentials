from contextvars import ContextVar
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "SOLL Credential API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    database_url: SecretStr = SecretStr("postgresql+pg8000://compat:compat@127.0.0.1/compat")
    otp_pepper: SecretStr = SecretStr("local-compatibility-placeholder")

    session_ttl_days: int = 7
    session_cookie_name: str = "soll_session"
    csrf_cookie_name: str = "soll_csrf"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    cors_origins: str = "http://localhost:3000"
    trusted_proxy_cidrs: str = ""

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from_email: str | None = None
    smtp_starttls: bool = True
    smtp_ssl: bool = False
    smtp_timeout_seconds: int = 10

    model_config = SettingsConfigDict(
        env_file=API_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]



_otp_pepper_context: ContextVar[str | None] = ContextVar(
    "otp_pepper",
    default=None,
)

def set_otp_pepper(value: str):
    return _otp_pepper_context.set(value)

def reset_otp_pepper(token) -> None:
    _otp_pepper_context.reset(token)

def get_otp_pepper() -> str:
    value = _otp_pepper_context.get()
    if value is not None:
        return value
    return settings.otp_pepper.get_secret_value()


settings = Settings()
