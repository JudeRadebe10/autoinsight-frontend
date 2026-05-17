import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AutoInsight ZA"
    PORT: int = 8765
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/autoinsight_db"
    
    # JWT Secrets
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production-long-random"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: str = "https://symphonious-palmier-e70423.netlify.app,http://localhost:3000,http://localhost:8765"
    
    # Seed Data
    SEED_SUPER_ADMIN_EMAIL: str = "superadmin@example.com"
    SEED_SUPER_ADMIN_PASSWORD: str = "SuperAdmin123!"
    SEED_ADMIN_EMAIL: str = "admin@example.com"
    SEED_ADMIN_PASSWORD: str = "Admin123!"
    SEED_CLIENT_EMAIL: str = "client@example.com"
    SEED_CLIENT_PASSWORD: str = "Client123!"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
