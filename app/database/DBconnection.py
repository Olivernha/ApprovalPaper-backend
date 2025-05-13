# app/database/mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient
from ..config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None
    
    @classmethod
    async def connect_to_database(cls):
        """Connect to MongoDB."""
        if cls.client is None:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            cls.database = cls.client[settings.DATABASE_NAME]
            print(f"Connected to MongoDB at {settings.MONGODB_URL}")
            print(f"Using database: {settings.DATABASE_NAME}")
    
    @classmethod
    async def close_database_connection(cls):
        """Close MongoDB connection."""
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.database = None
            print("Closed MongoDB connection")
    
    @classmethod
    def get_database(cls):
        """Get database instance."""
        return cls.database