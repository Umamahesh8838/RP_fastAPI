from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
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
try:
    import pymysql
    logger.info(f"✓ PyMySQL detected")
except ImportError as e:
    logger.error(f"✗ PyMySQL not installed: {e}")
    sys.exit(1)

# ──────────────────────────────────────────────────────────
# CREATE SYNCHRONOUS ENGINE FOR MYSQL 8.x
# ──────────────────────────────────────────────────────────
try:
    logger.info("Creating synchronous SQLAlchemy engine for MySQL 8.x...")
    logger.info("  Database driver: MySQL 8.x (PyMySQL)")
    logger.info("  Pool class: Default QueuePool (with connection pooling)")
    
    engine = create_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
        connect_args={
            "ssl": {"check_hostname": False}
        }
    )
    
    logger.info("✓ Synchronous engine created successfully")
    logger.info(f"  Connection: mysql+pymysql://{settings.db_user}@{settings.db_host}:{settings.db_port}/{settings.db_name}")
    
except Exception as e:
    logger.error(f"✗ Failed to create synchronous engine: {e}", exc_info=True)
    logger.error("  Check: PyMySQL installed? MySQL connection details correct?")
    sys.exit(1)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def get_db() -> Session:
    """
    FastAPI dependency that yields a synchronous DB session.
    Automatically closes session after request completes.
    Usage: db: Session = Depends(get_db)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
