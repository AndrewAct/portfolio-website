import certifi
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    mongodb_username: str
    mongodb_password: str
    mongodb_cluster: str
    mongodb_database: str
    is_development: bool = True  # Add this flag to control environment-specific settings

    @property
    def mongodb_url(self) -> str:
        base_url = (
            f"mongodb+srv://{self.mongodb_username}:{self.mongodb_password}"
            f"@{self.mongodb_cluster}/{self.mongodb_database}"
        )

        # Add query parameters based on environment
        if self.is_development:
            # Development environment: less strict SSL settings
            return f"{base_url}?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"
        else:
            # Production environment: proper SSL settings
            return f"{base_url}?retryWrites=true&w=majority&tls=true"


    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()