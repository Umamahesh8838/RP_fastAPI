from pydantic_settings import BaseSettings
from functools import lru_cache
from urllib.parse import quote_plus
import os


class Settings(BaseSettings):
    """All application settings loaded from .env file and environment variables."""

    # OpenRouter API
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")

    # Database - Priority: Environment Variables > .env file > defaults
    db_driver: str = os.getenv("DB_DRIVER", "mssql")  # mysql | mssql
    db_host: str = os.getenv("DB_HOST", "artisetsql.database.windows.net")
    db_port: int = int(os.getenv("DB_PORT", "1433"))
    db_user: str = os.getenv("DB_USER", "artiset")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_name: str = os.getenv("DB_NAME", "campus5")

    # App
    app_env: str = os.getenv("APP_ENV", "development")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    allowed_extensions: str = os.getenv("ALLOWED_EXTENSIONS", "pdf,docx")

    @property
    def database_url(self) -> str:
        """Builds async SQLAlchemy connection string for configured database engine."""
        driver = self.db_driver.lower().strip()

        if driver == "mssql":
            # Azure SQL connection string with pyodbc driver
            user = quote_plus(self.db_user)
            password = quote_plus(self.db_password)
            connection_string = (
                f"mssql+pyodbc://{user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"
                "?driver=ODBC+Driver+18+for+SQL+Server"
                "&Encrypt=yes"
                "&TrustServerCertificate=no"
                "&Connection+Timeout=120"
            )
            return connection_string

        mysql_user = quote_plus(self.db_user)
        mysql_password = quote_plus(self.db_password)
        return f"mysql+aiomysql://{mysql_user}:{mysql_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    def get_db_config_summary(self) -> dict:
        """Returns database configuration summary (without password)."""
        return {
            "driver": self.db_driver,
            "host": self.db_host,
            "port": self.db_port,
            "user": self.db_user,
            "database": self.db_name,
            "environment": self.app_env
        }

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
