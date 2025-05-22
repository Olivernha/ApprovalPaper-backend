from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from app.core.database import MongoDB
from app.models.department import DepartmentModel
from app.models.document import DocumentModel
from app.models.user import UserModel
from app.api.v1.routers import admin, department, document
from app.services.seed import seed_data
from app.core.config import settings
from app.core.logging import configure_logging

logger = configure_logging()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("Starting application...")
    try:
        logger.info("Connecting to MongoDB...")
        await MongoDB.connect_to_database()
        logger.info("Connected to MongoDB successfully")

        logger.info("Ensuring database indexes...")
        await DepartmentModel.ensure_indexes()
        await DocumentModel.ensure_indexes()
        await UserModel.ensure_indexes()
        logger.info("Database indexes ensured")

        if settings.SEED_DATA_ON_STARTUP:
            logger.info("Seeding initial data...")
            await seed_data()
            logger.info("Data seeding completed")

        yield
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise
    finally:
        logger.info("Closing MongoDB connection...")
        await MongoDB.close_database_connection()
        logger.info("Application shutdown complete")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Approval Paper Management API",
    lifespan=lifespan
)

app.include_router(admin.router)
app.include_router(department.router)
app.include_router(document.router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )