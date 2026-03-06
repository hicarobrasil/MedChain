import uuid
from sqlalchemy import (
    String,
    DateTime,
    Enum,
    Integer,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from datetime import datetime, timezone
import enum

from app.database import Base


# Enum baseado em inteiros para uso na API
class GenderEnum(enum.IntEnum):
    MALE = 0
    FEMALE = 1
    OTHER = 2


class PatientModel(Base):
    __tablename__ = "patient"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, index=True, default=uuid.uuid4
    )
    cellphone: Mapped[str] = mapped_column(String(15), unique=True)
    birth_date: Mapped[datetime] = mapped_column(DateTime)
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum))
    created_date: Mapped[datetime | None] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user: Mapped["UserModel"] = relationship()
    files: Mapped[list["FileModel"]] = relationship(back_populates="patient")
