from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.database import MongoDB
from app.routes import adminRoute, documentRoute, departmentRoute
from app.models.departmentModel import DepartmentModel
from app.models.documentModel import DocumentModel
from app.utils.seed import seed_data
from app.config.settings import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Lifespan event handler for FastAPI application"""
    try:
        logger.info("Starting application...")
        
        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        await MongoDB.connect_to_database()
        logger.info("Connected to MongoDB successfully")

        # Ensure indexes
        logger.info("Ensuring database indexes...")
        await DepartmentModel.ensure_indexes()
        await DocumentModel.ensure_indexes()
        logger.info("Database indexes ensured")

        # Seed data if configured
        if settings.SEED_DATA_ON_STARTUP:
            logger.info("Seeding initial data...")
            await seed_data()
            logger.info("Data seeding completed")

        yield
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise
        
    finally:
        # Cleanup
        logger.info("Closing MongoDB connection...")
        await MongoDB.close_database_connection()
        logger.info("Application shutdown complete")

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Document Management System API",
    lifespan=lifespan
)

# Include routers
app.include_router(departmentRoute.router)
app.include_router(adminRoute.router)
app.include_router(documentRoute.router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )