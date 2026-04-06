from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """All application settings loaded from .env file."""

    # OpenRouter API
    openrouter_api_key: str = "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"
    openrouter_model: str = "openai/gpt-3.5-turbo"

    # MySQL
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "campus5"

    # App
    app_env: str = "development"
    app_port: int = 8000
    max_file_size_mb: int = 10
    allowed_extensions: str = "pdf,docx"

    @property
    def database_url(self) -> str:
        """Builds async SQLAlchemy connection string for MySQL."""
        return f"mysql+aiomysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Returns cached settings instance."""
    return Settings()
