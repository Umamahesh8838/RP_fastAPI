from pydantic_settings import BaseSettings
from functools import lru_cache
from urllib.parse import quote_plus


class Settings(BaseSettings):
    """All application settings loaded from .env file."""

    # OpenRouter API
    openrouter_api_key: str = "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"
    openrouter_model: str = "openai/gpt-3.5-turbo"

    # Database
    db_driver: str = "mysql"  # mysql | mssql
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
        """Builds async SQLAlchemy connection string for configured database engine."""
        driver = self.db_driver.lower().strip()

        if driver == "mssql":
            # Azure SQL login usually expects username formatted as user@server.
            login_user = self.db_user
            if "@" not in login_user and self.db_host:
                login_user = f"{login_user}@{self.db_host.split('.')[0]}"

            user = quote_plus(login_user)
            password = quote_plus(self.db_password)
            return (
                f"mssql+aioodbc://{user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"
                "?driver=ODBC+Driver+18+for+SQL+Server"
                "&Encrypt=yes"
                "&TrustServerCertificate=yes"
                "&Connection+Timeout=120"
            )

        mysql_user = quote_plus(self.db_user)
        mysql_password = quote_plus(self.db_password)
        return f"mysql+aiomysql://{mysql_user}:{mysql_password}@{self.db_host}:{self.db_port}/{self.db_name}"

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
