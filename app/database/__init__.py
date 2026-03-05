from typing import Generator
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Session as SQLAlchemySession

from app.settings import Settings

settings = Settings()

# Remove parâmetros incompatíveis com PostgreSQL (ex: charset é opção MySQL)
_db_url = settings.SQLALCHEMY_DATABASE_URI
if _db_url and "charset" in _db_url.lower():
    parsed = urlparse(_db_url)
    query = parse_qs(parsed.query)
    for key in list(query.keys()):
        if key.lower() == "charset":
            del query[key]
    new_query = urlencode(query, doseq=True)
    _db_url = urlunparse(parsed._replace(query=new_query))

engine = create_engine(
    url=_db_url or settings.SQLALCHEMY_DATABASE_URI,
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
