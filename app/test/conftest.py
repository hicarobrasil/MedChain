import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient

# Configuração do banco de dados em memória para testes
# Usamos um engine por teste para garantir isolamento total sem complexidade de transações
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
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
