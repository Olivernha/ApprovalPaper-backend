# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings"""
    
    # MongoDB settings
    MONGODB_URL: str = os.getenv("MONGODB_URL")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME")
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    
    
settings = Settings()