"""
Configuração do banco de dados.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
get_db = SessionLocal

Base = declarative_base()

def init_db():
    """Inicializa o banco de dados."""
    Base.metadata.create_all(bind=engine)
    
