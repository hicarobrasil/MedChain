import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.settings import Settings

settings = Settings() 

# engine = create_engine(url=settings.SQLALCHEMY_DATABASE_URI)  INFERNOOOOO, VAI SE LASCAR

engine = create_engine(url='postgresql+psycopg2://postgres:0209@localhost:5432/medchain_db')

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
