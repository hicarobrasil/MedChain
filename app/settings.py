from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Geral
    APP_NAME: str = "FastAPI Auth Service"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Autenticacao
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutos
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600  # 1 hora

    # Dominio
    DOMAIN: str = "localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    # Banco de dados
    DATABASE_URL: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    DATABASE_ENVIRONMENT_SUFFIX: Optional[str] = None
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # Redis
    REDIS_URL: str
    REDIS_PASSWORD: Optional[str] = None

    # Amazon S3
    MEDICAL_RECORDS_API_AMAZON_S3_ACCESS_KEY_ID: str
    MEDICAL_RECORDS_API_AMAZON_S3_SECRET_ACCESS_KEY: str
    MEDICAL_RECORDS_API_AMAZON_S3_MEDICAL_RECORD_FILES_BUCKET_ID: str

    # E-mail
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str

    # Blockchain (Solana)
    ENABLE_BLOCKCHAIN: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"  # Garante leitura correta de acentos no .env
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
