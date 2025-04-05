from pydantic import BaseSettings


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str
    AMAZON_S3_ACESS_KEY: str
    AMAZON_S3_MEDICAL_RECORDS_BUCKET_ID: str
    AMAZON_S3_SECRET_ACCESS_KEY: str


settings = Settings()