from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from database import engine, AsyncSessionLocal, Base
import time
import os
from datetime import datetime
from routers.extract_router import router as extract_router
from routers.parse_router import router as parse_router
from routers.lookup_router import router as lookup_router
from routers.save_router import router as save_router
from routers.orchestrator_router import router as orchestrator_router
from models import *  # Import all models so they're registered with Base metadata
import logging
from config import get_settings
from database import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store server start time
SERVER_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    logger.info("✓ Application started successfully!")
    yield
    # Shutdown
    await engine.dispose()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Resume Parser API",
    description="Automatically fills campus5 database from resume files using LLM parsing.",        
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)

# Add CORS middleware with Azure Web App support
settings = get_settings()

# Determine allowed origins based on environment
if settings.app_env == "production":
    # For production on Azure, add your actual domain
    allowed_origins = [
        "https://your-azure-domain.azurewebsites.net",  # Update with your actual Azure domain
        "https://*.azurewebsites.net",  # Allow any Azure Web App subdomain for testing
    ]
else:
    # Development environments
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(extract_router,      prefix="/extract",  tags=["Extract"])
app.include_router(parse_router,        prefix="/parse",    tags=["Parse"])
app.include_router(lookup_router,       prefix="/lookup",   tags=["Lookup"])
app.include_router(save_router,         prefix="/save",     tags=["Save"])
app.include_router(orchestrator_router, prefix="/resume",   tags=["Resume"])


@app.get("/health")
async def health_check():
    """
    Detailed health check showing real-time status 
    of every system component.
    Returns overall status and individual component statuses.
    """
    
    settings = get_settings()
    results = {}
    overall_status = "ok"
    
    # ── 1. DATABASE CHECK ────────────────────────────
    db_start = time.time()
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        db_elapsed = round(time.time() - db_start, 3)
        results["database"] = {
            "status": "connected",
            "response_time_ms": round(db_elapsed * 1000),
            "host": settings.db_host,
            "name": settings.db_name
        }
    except Exception as e:
        db_elapsed = round(time.time() - db_start, 3)
        results["database"] = {
            "status": "disconnected",
            "response_time_ms": round(db_elapsed * 1000),
            "error": str(e)[:100]
        }
        overall_status = "degraded"
    
    # ── 2. OPENROUTER CHECK ─────────────────────────────
    if settings.openrouter_api_key:
        results["openrouter"] = {
            "status": "configured",
            "model": settings.openrouter_model,
            "note": "Use /resume/test-openrouter for live test"
        }
    else:
        results["openrouter"] = {
            "status": "not_configured",
            "error": "OPENROUTER_API_KEY is missing from .env"
        }
        overall_status = "degraded"
    
    # ── 3. CACHE CHECK ───────────────────────────────
    try:
        from utils.cache_utils import list_cache_files
        cached_files = list_cache_files()
        cache_dir = "resume_cache"
        
        # Calculate cache folder size
        total_size = 0
        if os.path.exists(cache_dir):
            for f in os.listdir(cache_dir):
                fp = os.path.join(cache_dir, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
        
        results["cache"] = {
            "status": "ok",
            "cached_resumes": len(cached_files),
            "folder": cache_dir,
            "size_kb": round(total_size / 1024, 1)
        }
    except Exception as e:
        results["cache"] = {
            "status": "error",
            "error": str(e)[:100]
        }
    
    # ── 4. FILE EXTRACTION CHECK ─────────────────────
    try:
        import fitz  # PyMuPDF
        import docx
        results["file_extraction"] = {
            "status": "ok",
            "pdf_support": "PyMuPDF",
            "docx_support": "python-docx",
            "supported_formats": ["pdf", "docx"],
            "max_file_size_mb": settings.max_file_size_mb
        }
    except ImportError as e:
        results["file_extraction"] = {
            "status": "degraded",
            "error": f"Missing library: {str(e)}"
        }
        overall_status = "degraded"
    
    # ── 5. STUDENT COUNT FROM DB ─────────────────────
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text("SELECT COUNT(*) FROM tbl_cp_student")
            )
            student_count = result.scalar()
            
            result2 = await db.execute(
                text("SELECT COUNT(*) FROM tbl_cp_resume_hashes")
            )
            resume_count = result2.scalar()
        
        results["database_stats"] = {
            "total_students": student_count,
            "total_resumes_processed": resume_count
        }
    except Exception as e:
        results["database_stats"] = {
            "error": "Could not fetch stats: " + str(e)[:80]
        }
    
    # ── 6. UPTIME ────────────────────────────────────
    uptime_seconds = round(time.time() - SERVER_START_TIME)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    results["server"] = {
        "status": "running",
        "uptime": f"{hours}h {minutes}m {seconds}s",
        "uptime_seconds": uptime_seconds,
        "started_at": datetime.fromtimestamp(
            SERVER_START_TIME
        ).strftime("%Y-%m-%d %H:%M:%S"),
        "current_time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }
    
    # ── FINAL RESPONSE ───────────────────────────────
    print(f"[HEALTH] Status: {overall_status}")
    print(f"[HEALTH] DB: {results['database']['status']}")
    print(f"[HEALTH] Cache: {results['cache'].get('cached_resumes', 0)} files")
    print(f"[HEALTH] Students in DB: {results.get('database_stats', {}).get('total_students', 'unknown')}")
    
    return {
        "status": overall_status,
        "version": "2.0",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "components": results
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Resume Parser API",
        "version": "1.0.0",
        "description": "FastAPI-based Resume Parsing System",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


@app.post("/admin/init-database")
async def init_database():
    """
    Initialize the database schema.
    Creates all tables from SQLAlchemy models.
    Safe to call multiple times - idempotent.
    """
    try:
        logger.info("Initializing database schema...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✓ Database schema initialized successfully!")
        return {
            "status": "success",
            "message": "All tables created or verified",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

