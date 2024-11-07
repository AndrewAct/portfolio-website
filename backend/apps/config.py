from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    mongodb_username: str
    mongodb_password: str
    mongodb_cluster: str
    mongodb_database: str

    @property
    def mongodb_url(self) -> str:
        return (
            f"mongodb+srv://{self.mongodb_username}:{self.mongodb_password}"
            f"@{self.mongodb_cluster}/{self.mongodb_database}"
            "?retryWrites=true&w=majority"
            "&tlsAllowInvalidCertificates=true"  # Disable SSL Certificate: not recommended, but it helps when I connect
        )

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()