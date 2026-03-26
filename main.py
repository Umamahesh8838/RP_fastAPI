from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from database import engine, AsyncSessionLocal
from routers.extract_router import router as extract_router
from routers.parse_router import router as parse_router
from routers.lookup_router import router as lookup_router
from routers.save_router import router as save_router
from routers.orchestrator_router import router as orchestrator_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    # Startup: create tbl_cp_resume_hashes if not exists
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS tbl_cp_resume_hashes (
                    hash       VARCHAR(64)  NOT NULL PRIMARY KEY,
                    student_id INT          NOT NULL,
                    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP
                )
            """))
            await db.commit()
        logger.info("Startup complete. tbl_cp_resume_hashes ensured.")
    except Exception as e:
        logger.error(f"Error creating resume_hashes table: {e}")
    
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
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
    """Health check endpoint."""
    return {"status": "ok", "message": "Resume Parser API is running"}


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
