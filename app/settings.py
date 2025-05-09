from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    # WORKSPACE: str
    # AMAZON_S3_ACCESS_KEY: Optional[str]
    # AMAZON_S3_SECRET_ACCESS_KEY: Optional[str]
    # AMAZON_S3_MEDICAL_RECORDS_BUCKET_ID: Optional[str]

settings = Settings()