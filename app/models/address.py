import uuid
from app.database import Base
from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone


class AddressModel(Base):
    __tablename__ = "address"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, index=True, default=uuid.uuid4
    )
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
