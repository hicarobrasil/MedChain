from sqlalchemy import (
    String,
    DateTime,
    Enum,
    Integer,
    ForeignKey,
)
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

    cellphone: Mapped[str] = mapped_column(String(15), primary_key=True, unique=True)
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
