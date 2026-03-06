import sys
from typing import Generator
from urllib.parse import quote_plus

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Session as SQLAlchemySession

from app.settings import Settings

settings = Settings()

# No Windows fora do Docker, "postgres" nao resolve
host = (
    "localhost"
    if (sys.platform == "win32" and settings.POSTGRES_HOST == "postgres")
    else settings.POSTGRES_HOST
)
suffix = settings.DATABASE_ENVIRONMENT_SUFFIX or ""
dbname = f"medchain_db{suffix}"
user = quote_plus(settings.POSTGRES_USER)
password = quote_plus(settings.POSTGRES_PASSWORD)
# psycopg (v3) tem melhor suporte a encoding no Windows que psycopg2
database_url = (
    f"postgresql+psycopg://{user}:{password}@{host}:{settings.POSTGRES_PORT}/{dbname}"
)

engine = create_engine(
    database_url,
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


get_db = get_session  # alias para compatibilidade


def init_db() -> None:
    """Cria as tabelas no banco de dados. Importa os models para registra-los no Base."""
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
