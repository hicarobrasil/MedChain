from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    # Geral
    APP_NAME: str = "FastAPI Auth Service"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Autenticação
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # 30 minutos
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600 # 1 hora

    # Domínio
    DOMAIN: str = "localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    # Banco de dados
    DATABASE_URL: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str 

    # Redis
    REDIS_URL: str
    REDIS_PASSWORD: Optional[str] = None

    # E-mail
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
