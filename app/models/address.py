from uuid import UUID
from app.database import Base
from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone


class AddressModel(Base):
    __tablename__ = "address"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(UUID, unique=True, index=True)
    street: Mapped[str] = mapped_column(String)
    number: Mapped[str] = mapped_column(String)
    complement: Mapped[str | None] = mapped_column(String, nullable=True)
    neighborhood: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    created_date: Mapped[datetime | None] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient.id"))
    patient: Mapped["PatientModel"] = relationship()
