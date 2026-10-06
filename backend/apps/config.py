from functools import lru_cache
from urllib.parse import quote_plus, urlencode

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_username: str
    mongodb_password: str
    mongodb_cluster: str
    mongodb_database: str
    is_development: bool = True  # Add this flag to control environment-specific settings

    environment: str = "development"

    # Add variables for DeepSeek API key, OpenAI API KEY, Gemini API KEY
    deepseek_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    gemini_timeout_seconds: int = 15

    # Neon Postgres — horoscope email subscriptions (separate from the MongoDB URL shortener store)
    database_url: str

    # Resend — outbound email for confirmation and daily horoscope delivery
    resend_api_key: str
    resend_from_email: str
    # From_email isn't a real inbox — Reply-To gives subscribers a real address to
    # reach; optional/blank omits the header entirely rather than sending an empty one.
    resend_reply_to_email: str = ""
    resend_webhook_secret: str
    resend_timeout_seconds: int = 15

    # HMAC secret signing confirm/preferences/unsubscribe links; never persisted
    subscription_token_secret: str
    confirm_token_ttl_days: int = 7

    # Base URL used to build links embedded in outbound emails
    public_base_url: str = "https://andrewcee.io"

    # Horoscope email worker polling loop. Every tick is a real SELECT against Neon's
    # direct endpoint — anything under ~5min keeps compute perpetually active and defeats
    # scale-to-zero (confirmed 2026-08-17: 60s polling produced ~24/7 active billing,
    # ~180 CU-hr/month). 900s (15min) trades up to 15min of delivery-time slack (fine for
    # a once-daily email) for an estimated ~3x cut, to ~60 CU-hr/month.
    worker_poll_interval_seconds: int = 900
    worker_max_delivery_attempts: int = 5
    # A delivery stuck at status='pending' longer than this was almost certainly
    # abandoned by a worker process killed mid-send (e.g. SIGKILL during a deploy, no
    # signal handler catches it) rather than one that's still legitimately in flight —
    # eligible for reclaim on the next tick.
    worker_stale_pending_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",  # Allow extra env variables
        case_sensitive=False,
    )

    @property
    def mongodb_url(self) -> str:
        username = quote_plus(self.mongodb_username)
        password = quote_plus(self.mongodb_password)
        options = urlencode(
            {
                "appName": "Cluster0",
                "retryWrites": "true",
                "w": "majority",
                "tls": "true",
            }
        )
        return f"mongodb+srv://{username}:{password}@{self.mongodb_cluster}/?{options}"

    # model config and class config cannot be used together
    # class Config:
    #     env_file = ".env"
    #     case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
