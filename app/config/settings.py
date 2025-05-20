# app/config/settings.py
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    PROJECT_NAME: str = "Approval Paper System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "document_management"
    API_V1_PREFIX: str = "/api/v1"
    SEED_DATA_ON_STARTUP: bool = False  # Set to True to seed data on startup
    GRIDFS_BUCKET_NAME: str = "attachment"  # Replace with your actual bucket name

    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()