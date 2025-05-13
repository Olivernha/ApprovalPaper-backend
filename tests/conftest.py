import pytest_asyncio
from app.config import Settings
from dotenv import load_dotenv
import os

# Load test environment variables
load_dotenv()

# Override settings for testing
def pytest_configure():
    os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
    os.environ["DATABASE_NAME"] = "test_db"

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()