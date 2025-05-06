import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Carrega variáveis de ambiente, se estiver usando .env
load_dotenv()

# URL do banco (pode continuar vindo do ENV)
# SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI")
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:0209@localhost:5432/medchain_db"

# Cria o engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Cria o SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()

def init_db():
    """Cria as tabelas caso não existam."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Dependência do FastAPI para obter uma sessão de DB.
    Gera e depois fecha a sessão automaticamente.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
