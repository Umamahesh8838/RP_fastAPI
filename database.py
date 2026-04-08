from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from config import get_settings
import logging
import sys

logger = logging.getLogger(__name__)
settings = get_settings()

# ──────────────────────────────────────────────────────────
# STARTUP DIAGNOSTICS
# ──────────────────────────────────────────────────────────
def log_startup_info():
    """Log database configuration at startup for debugging."""
    config = settings.get_db_config_summary()
    logger.info("=" * 70)
    logger.info("DATABASE CONFIGURATION")
    logger.info("=" * 70)
    for key, value in config.items():
        logger.info(f"  {key:15} : {value}")
    logger.info("=" * 70)

log_startup_info()

# ──────────────────────────────────────────────────────────
# VERIFY SYSTEM REQUIREMENTS
# ──────────────────────────────────────────────────────────
if settings.db_driver == "mssql":
    try:
        import pyodbc
        logger.info(f"✓ pyodbc version {pyodbc.version} detected")
        
        # Check for ODBC drivers
        drivers = pyodbc.drivers()
        mssql_drivers = [d for d in drivers if "Driver" in d and "SQL" in d]
        
        if mssql_drivers:
            logger.info(f"✓ SQL Server ODBC drivers found: {mssql_drivers}")
        else:
            logger.warning("⚠️  No SQL Server ODBC drivers found!")
            logger.warning("   Install: 'ODBC Driver 18 for SQL Server'")
            logger.warning("   On Linux/Azure App Service, add to deployment:")
            logger.warning("   apt-get install -y odbc-driver-18-for-sql-server")
    except ImportError as e:
        logger.error(f"✗ pyodbc not installed: {e}")
        sys.exit(1)

# ──────────────────────────────────────────────────────────
# CREATE ASYNC ENGINE FOR AZURE SQL
# ──────────────────────────────────────────────────────────
try:
    logger.info("Creating async SQLAlchemy engine...")
    
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        poolclass=NullPool if settings.db_driver == "mssql" else None,
        pool_size=5,
        max_overflow=10,
    )
    
    logger.info("✓ Async engine created successfully")
    logger.info(f"  Connection string: {settings.database_url[:80]}...")
    
except Exception as e:
    logger.error(f"✗ Failed to create engine: {e}", exc_info=True)
    sys.exit(1)

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
