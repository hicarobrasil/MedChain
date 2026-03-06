import uuid
from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from datetime import datetime, timezone
from enum import Enum

from app.database import Base


class SpecialtyEnum(Enum):
    CARDIOLOGY = "CARDIOLOGY"
    DERMATOLOGY = "DERMATOLOGY"
    NEUROLOGY = "NEUROLOGY"
    PEDIATRICS = "PEDIATRICS"
    PSYCHIATRY = "PSYCHIATRY"
    ORTHOPEDICS = "ORTHOPEDICS"
    GENERAL = "GENERAL"
    OTHER = "OTHER"


class DoctorModel(Base):
    __tablename__ = "doctor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, index=True, default=uuid.uuid4
    )
    CRM: Mapped[str] = mapped_column(String(20), unique=True)
    specialty: Mapped[SpecialtyEnum] = mapped_column(SQLEnum(SpecialtyEnum))
    created_date: Mapped[datetime | None] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["UserModel"] = relationship()
    files: Mapped[list["FileModel"]] = relationship(back_populates="doctor")
