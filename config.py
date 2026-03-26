from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """All application settings loaded from .env file."""

    # Anthropic (Legacy - if using cloud API)
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 4096
    claude_temperature: float = 0.0

    # Ollama model (can be local or cloud-qualified name)
    # To use cloud-hosted model set this to the cloud-qualified model name, e.g. "minimax-m2.7:cloud"
    ollama_model: str = "minimax-m2.7:cloud"
    # Base URL for Ollama-compatible API (keep as localhost when using local server)
    ollama_base_url: str = "http://localhost:11434"

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
