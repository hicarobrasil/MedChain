import pytest
import uuid
import os

# Set dummy environment variables for testing
os.environ["JWT_SECRET"] = "this-is-a-very-long-secret-key-that-is-at-least-32-chars-long"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
# Disable background tasks
os.environ["DISABLE_BACKGROUND_TASKS"] = "1"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_USER"] = "test"
os.environ["POSTGRES_PASSWORD"] = "test"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["MEDICAL_RECORDS_API_AMAZON_S3_ACCESS_KEY_ID"] = "test"
os.environ["MEDICAL_RECORDS_API_AMAZON_S3_SECRET_ACCESS_KEY"] = "test"
os.environ["MEDICAL_RECORDS_API_AMAZON_S3_MEDICAL_RECORD_FILES_BUCKET_ID"] = "test"
os.environ["SMTP_SERVER"] = "localhost"
os.environ["SMTP_PORT"] = "25"
os.environ["SMTP_USER"] = "test"
os.environ["SMTP_PASSWORD"] = "test"
os.environ["EMAIL_FROM"] = "test"
os.environ["MEDICAL_RECORDS_API_CRYPTO_KEY"] = "Jjthyc8s3G18ZiSIHJbZnnuziy3Wh9I7TFjmc9jI6ag="

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock

from app.database import Base, get_db, get_session
from app.views.medical_record_api import router as medical_record_api_router
with patch("app.database.init_db"):
    from app.main import app
    app.include_router(medical_record_api_router, prefix="/api/v1")
from fastapi.testclient import TestClient
from app.auth import User, UserRole, AuthenticatedUser, get_user
from app.dependencies import admin_only, user_or_admin

# Mock user for tests
@pytest.fixture
def mock_admin_user():
    user = MagicMock(spec=AuthenticatedUser)
    user.role = UserRole.ADMIN
    user.email = "admin@test.com"
    user.public_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    user.is_authenticated = True
    return user

@pytest.fixture
def mock_doctor_user():
    user = MagicMock(spec=AuthenticatedUser)
    user.role = UserRole.DOCTOR
    user.email = "doctor@test.com"
    user.public_id = uuid.UUID("660e8400-e29b-41d4-a716-446655440000")
    user.is_authenticated = True
    return user

@pytest.fixture
def mock_patient_user():
    user = MagicMock(spec=AuthenticatedUser)
    user.role = UserRole.PATIENT
    user.email = "patient@test.com"
    user.public_id = uuid.UUID("770e8400-e29b-41d4-a716-446655440000")
    user.is_authenticated = True
    return user

@pytest.fixture
def db_session():
    """
    Cria um novo banco de dados em memória e uma sessão para cada teste.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture
def client(db_session):
    """
    Fixture para o cliente de teste do FastAPI, injetando a sessão de banco de dados de teste.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_session] = override_get_db
    
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def authenticated_client(client, mock_admin_user):
    """
    Fixture que retorna um cliente com o dependência de usuário mockada como Admin.
    """
    app.dependency_overrides[get_user] = lambda: mock_admin_user
    app.dependency_overrides[admin_only] = lambda: True
    app.dependency_overrides[user_or_admin] = lambda: True
    return client
