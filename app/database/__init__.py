from typing import Generator

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Session as SQLAlchemySession

from app.settings import Settings

settings = Settings()


engine = create_engine(
    url=settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_use_lifo=True,
    pool_size=30,
    max_overflow=15,
    pool_recycle=1800,
    connect_args={"charset": "utf8mb4"},
)

# Cria o SessionLocal
Session = sessionmaker(engine)


def get_session() -> Generator[SQLAlchemySession, None, None]:
    with Session.begin() as session:
        yield session


class Base(DeclarativeBase):
    def delete(self):
        session = inspect(self).session
        session.delete(self)
        session.commit()

    def __repr__(self):
        return f"<{self.__class__.__name__} { self.id}>"
