from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List

class Settings(BaseSettings):
    # Project Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{DATA_DIR}/processed/grc_analytics.db"
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "GRC Analytics API"
    
    # Security
    # In production, this should be set to specific origins via env var
    # e.g. export CORS_ORIGINS='["http://localhost:3000", "https://myapp.com"]'
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
