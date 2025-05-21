from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None
    
    @classmethod
    async def connect_to_database(cls):
        """Connect to MongoDB and verify connection."""
        if cls.client is None:
            try:
                cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
                # Test connection by accessing the database
                cls.database = cls.client[settings.DATABASE_NAME]
                # Verify connection with a simple command
                await cls.database.command("ping")
                logger.info(f"Successfully connected to MongoDB at {settings.MONGODB_URL}")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB at {settings.MONGODB_URL}: {str(e)}")
                cls.client = None
                cls.database = None
                raise Exception(f"MongoDB connection failed: {str(e)}")
    
    @classmethod
    async def close_database_connection(cls):
        """Close MongoDB connection."""
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.database = None
            logger.info("Closed MongoDB connection")
    
    @classmethod
    def get_database(cls):
        """Get database instance."""
        return cls.database