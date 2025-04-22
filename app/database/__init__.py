import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI") 

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:0209@localhost:52730/medchain_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
get_db = SessionLocal

Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
