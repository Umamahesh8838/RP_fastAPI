#!/usr/bin/env python3
"""
Azure App Service startup script for FastAPI application.
This script prepares the environment and starts the ASGI server.
"""

import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Main startup routine for Azure App Service."""
    logger.info("=" * 70)
    logger.info("🚀 FastAPI Application Startup (Azure App Service)")
    logger.info("=" * 70)
    
    # Step 1: Verify environment
    logger.info("Step 1: Verifying environment...")
    
    # Check required environment variables
    required_vars = ["DB_DRIVER", "DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("   Please add these to Azure Portal → Configuration → Application settings")
    else:
        logger.info("✓ All required environment variables set")
    
    # Step 2: Verify Python dependencies
    logger.info("\nStep 2: Verifying Python dependencies...")
    try:
        import pyodbc
        logger.info(f"✓ pyodbc {pyodbc.version} installed")
    except ImportError:
        logger.error("✗ pyodbc not installed - installing now...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyodbc"], check=True)
        logger.info("✓ pyodbc installed")
    
    # Step 3: Check ODBC drivers (Linux/Azure specific)
    logger.info("\nStep 3: Checking ODBC drivers...")
    if os.path.exists("/etc/os-release"):
        # We're on Linux (Azure)
        try:
            import pyodbc
            drivers = pyodbc.drivers()
            mssql_drivers = [d for d in drivers if "Driver" in d and "SQL" in d]
            
            if mssql_drivers:
                logger.info(f"✓ SQL Server ODBC drivers found: {mssql_drivers}")
            else:
                logger.warning("⚠️  No SQL Server ODBC drivers found")
                logger.warning("   Attempting to install ODBC Driver 18...")
                # This would need to be done during container build, not at runtime
                logger.warning("   (Run apt-get install -y msodbcsql18 during deployment)")
        except Exception as e:
            logger.warning(f"Could not check ODBC drivers: {e}")
    else:
        # Windows
        logger.info("Windows system detected")
    
    # Step 4: Test configuration loading
    logger.info("\nStep 4: Loading configuration...")
    try:
        from config import get_settings
        settings = get_settings()
        config_summary = settings.get_db_config_summary()
        logger.info("✓ Settings loaded successfully")
        for key, value in config_summary.items():
            if key != "database":
                logger.info(f"  {key}: {value}")
    except Exception as e:
        logger.error(f"✗ Failed to load settings: {e}")
        sys.exit(1)
    
    # Step 5: Start the FastAPI application
    logger.info("\nStep 5: Starting FastAPI application...")
    logger.info("=" * 70)
    
    port = int(os.getenv("PORT", 8000))
    
    # Import and run the app
    try:
        import uvicorn
        
        logger.info(f"Starting uvicorn on port {port}")
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
            reload=False  # Never use reload in production
        )
    except ImportError:
        logger.error("uvicorn not installed - installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "uvicorn"], check=True)
        import uvicorn
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
            reload=False
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
