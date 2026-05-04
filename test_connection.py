#!/usr/bin/env python3
"""Quick test of MySQL connection and application startup."""

import sys
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from database import SessionLocal, engine
    from config import get_settings
    
    settings = get_settings()
    logger.info("=" * 70)
    logger.info("TESTING MySQL CONNECTION")
    logger.info("=" * 70)
    logger.info(f"Host: {settings.db_host}")
    logger.info(f"Port: {settings.db_port}")
    logger.info(f"Database: {settings.db_name}")
    logger.info(f"User: {settings.db_user}")
    
    # Test connection
    session = SessionLocal()
    result = session.execute(text("SELECT 1 as test"))
    logger.info("✓ MySQL Connection SUCCESSFUL")
    session.close()
    
    logger.info("=" * 70)
    logger.info("✓ DATABASE IS READY FOR DEPLOYMENT")
    logger.info("=" * 70)
    sys.exit(0)
    
except Exception as e:
    logger.error(f"✗ Connection failed: {e}", exc_info=True)
    sys.exit(1)
