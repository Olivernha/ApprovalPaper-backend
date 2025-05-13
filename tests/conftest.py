import pytest_asyncio
from app.database.DBconnection import MongoDB
from dotenv import load_dotenv
import os
import uuid


# Load test environment variables from .env
load_dotenv()
def pytest_configure():
   
    os.environ["MONGODB_URL"] = os.getenv("TEST_MONGODB_URL")
    os.environ["DATABASE_NAME"] = os.getenv("TEST_DATABASE_NAME")

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def test_db():
    """Set up a MongoDB Atlas test database."""
    await MongoDB.connect_to_database()
    db = MongoDB.get_database()
    yield db
    await MongoDB.close_database_connection()

@pytest_asyncio.fixture
async def test_collection_name():
    """Generate a unique collection name for tests."""
    return f"test_users_{uuid.uuid4().hex}"