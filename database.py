from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# For Azure SQL Server with pyodbc, use NullPool for better connection handling
# This prevents connection pooling issues in serverless environments
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    poolclass=NullPool if settings.db_driver == "mssql" else None,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields an async DB session.
    Automatically closes session after request completes.
    Usage: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
