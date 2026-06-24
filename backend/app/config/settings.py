import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or defaults.
    """
    # API Configurations
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Dataset Quality Checker and Preprocessor API"
    
    # Storage & Upload Configurations
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB in bytes
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".json", ".parquet"]
    
    # Session Configurations
    SESSION_TIMEOUT: int = 3600  # 1 hour in seconds
    MAX_HISTORY: int = 50       # Max undo history depth
    ENABLE_AI: bool = False
    
    # Directories
    STORAGE_DIR: str = "app/storage"
    UPLOADS_DIR: str = "app/storage/uploads"
    CLEANED_DIR: str = "app/storage/cleaned"
    REPORTS_DIR: str = "app/storage/reports"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        # Vite dev server (default port 5173)
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # Custom Vite port configured in vite.config.ts
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        # CRA / other common dev ports
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Supabase & Auth
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    JWT_SECRET: str
    SECRET_KEY: str
    
    # AI Providers
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    MISTRAL_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
for directory in [settings.STORAGE_DIR, settings.UPLOADS_DIR, settings.CLEANED_DIR, settings.REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)
