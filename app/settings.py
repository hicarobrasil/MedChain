from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Required fields
    SQLALCHEMY_DATABASE_URI: str
    JWT_SECRET: str
    
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    domain: str = "localhost:8000"
    frontend_url: str = "http://localhost:3000"
    
    database_url: str
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str
    
    # Redis Configuration
    redis_url: str
    redis_password: str
    
    # Email Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    email_from: str
    
    # Use model_config instead of Config class for Pydantic v2
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        # Allow extra fields if you want flexibility
        extra="allow"  # or "ignore" to ignore extra fields, or "forbid" to raise errors
    )

# Create settings instance
settings = Settings()