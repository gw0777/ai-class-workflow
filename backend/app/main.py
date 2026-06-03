from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from pathlib import Path

from .config import settings
from .database import create_tables

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting up application...")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Not configured'}")

    # Ensure upload directory exists
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # Create tables (in production, use Alembic migrations instead)
    if settings.DEBUG:
        logger.info("Creating database tables...")
        await create_tables()

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Activity Tracker API",
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION
    }


# Import and include routers
from .routers import auth, activities, users, documents

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(activities.router, prefix="/api/v1/activities", tags=["Activities"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])

# TODO: Add these routers later
# from .routers import locations, analysis
# app.include_router(locations.router, prefix="/api/v1/locations", tags=["Locations"])
# app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
