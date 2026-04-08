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
    logger.info("Creating async SQLAlchemy engine for Azure SQL...")
    
    if settings.db_driver == "mssql":
        # For MSSQL with aioodbc: Use aioodbc + pyodbc for true async support
        # aioodbc wraps pyodbc and provides async/await interface
        logger.info("  Database driver: SQL Server (aioodbc)")
        logger.info("  Pool class: NullPool (no connection pooling - optimal for serverless)")
        
        engine = create_async_engine(
            settings.database_url,
            echo=False,
            future=True,
            poolclass=NullPool,
            # NullPool-compatible parameters only
            connect_args={
                "timeout": 30,
                "check_same_thread": False,
                "autocommit": False,
            }
        )
    else:
        # For MySQL with aiomysql: Use default connection pool
        logger.info("  Database driver: MySQL (aiomysql)")
        logger.info("  Pool class: Default QueuePool (with connection pooling)")
        
        engine = create_async_engine(
            settings.database_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    
    logger.info("✓ Async engine created successfully")
    logger.info(f"  Connection: {settings.db_driver.upper()}://{settings.db_user}@{settings.db_host}:{settings.db_port}/{settings.db_name}")
    
except TypeError as e:
    logger.error(f"✗ Engine configuration TypeError: {e}")
    logger.error("  Incompatible parameters for the selected pool class")
    logger.error("  pool_size/max_overflow only valid with connection pooling")
    logger.error("  With NullPool, use only: connect_args, echo, future, poolclass")
    sys.exit(1)
    
except Exception as e:
    logger.error(f"✗ Failed to create async engine: {e}", exc_info=True)
    logger.error("  Check: aioodbc installed? ODBC Driver 18 available?")
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
