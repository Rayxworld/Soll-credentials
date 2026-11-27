from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "SOLL Credential API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    database_url: SecretStr
    otp_pepper: SecretStr

    session_ttl_days: int = 7
    session_cookie_name: str = "soll_session"
    csrf_cookie_name: str = "soll_csrf"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    cors_origins: str = "http://localhost:3000,https://soll-credentials.vercel.app"
    trusted_proxy_cidrs: str = ""

    resend_api_key: SecretStr | None = None
    resend_from_email: str | None = None
    resend_timeout_seconds: int = 15

    # Soroban is deliberately disabled until the deployment supplies an
    # explicit RPC endpoint, network passphrase, and contract ID.
    soroban_rpc_url: str | None = None
    soroban_network_passphrase: str | None = None
    soroban_contract_id: str | None = None
    stellar_network: str = "testnet"

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


settings = Settings()
