import os
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Step 1: Always load .env first
load_dotenv(".env")
env = os.getenv("ENVIRONMENT", "production")

# Step 2: Decide which file to load next
env_file_map = {
    "development": ".env.dev",
    "production": ".env.prod",
}

env_file = env_file_map.get(env, ".env.prod")  # Fallback to prod

print(f"🔧 Loading environment: {env}, file: {env_file}")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Approval Paper Management API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = env
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "approval_db"
    GRIDFS_BUCKET_NAME: str = "fs"
    SEED_DATA_ON_STARTUP: bool = False
    CORS_ORIGINS: List[str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8"
    )

settings = Settings()
