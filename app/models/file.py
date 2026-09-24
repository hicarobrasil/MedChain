import uuid
from datetime import datetime, timezone

from app.database import Base
from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class FileModel(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    format: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    blockchain_tx_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_date: Mapped[datetime | None] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=True
    )
    patient_uid: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("patient.public_id")
    )
    patient: Mapped["PatientModel"] = relationship(back_populates="files")
    doctor_uid: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("doctor.public_id")
    )
    doctor: Mapped["DoctorModel"] = relationship(back_populates="files")
