import os
from typing import Generator
from urllib.parse import quote_plus

# Força UTF-8 para evitar UnicodeDecodeError em credenciais com acentos
os.environ.setdefault("PGCLIENTENCODING", "UTF8")

import psycopg2
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Session as SQLAlchemySession

from app.settings import Settings

settings = Settings()


def _create_connection():
    """Cria conexão via DSN com encoding seguro para senhas com acentos."""
    suffix = settings.DATABASE_ENVIRONMENT_SUFFIX or ""
    dbname = f"medchain_db{suffix}"
    # URL-encode evita UnicodeDecodeError com caracteres especiais (ã, ç, etc.)
    user = quote_plus(settings.POSTGRES_USER)
    password = quote_plus(settings.POSTGRES_PASSWORD)
    dsn = f"postgresql://{user}:{password}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{dbname}"
    return psycopg2.connect(dsn, options="-c client_encoding=UTF8")


engine = create_engine(
    "postgresql+psycopg2://",
    creator=_create_connection,
    pool_pre_ping=True,
    pool_use_lifo=True,
    pool_size=30,
    max_overflow=15,
    pool_recycle=1800,
)

# Cria o SessionLocal
Session = sessionmaker(engine)


def get_session() -> Generator[SQLAlchemySession, None, None]:
    with Session.begin() as session:
        yield session


def init_db() -> None:
    """Cria as tabelas no banco de dados. Importa os models para registrá-los no Base."""
    from app.models import (  # noqa: F401
        address,
        consultation,
        doctor,
        file,
        login_record,
        medical_record,
        patient,
        prescription,
        prescription_item,
        user,
    )

    Base.metadata.create_all(bind=engine)


class Base(DeclarativeBase):
    def delete(self):
        session = inspect(self).session
        session.delete(self)
        session.commit()

    def __repr__(self):
        return f"<{self.__class__.__name__} { self.id}>"
