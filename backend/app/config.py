from __future__ import annotations
"""
app/config.py — Application settings loaded from environment variables.
Uses pydantic-settings to validate and type-coerce all config at startup.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str

    # Auth / JWT
    secret_key: str
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    # Email
    email_provider: str = "smtp"  # "resend" | "smtp"
    resend_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@goexpressly.com"

    # Public site URL (used for email logo images, tracking links, etc.)
    site_url: str = "https://goexpressly.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
