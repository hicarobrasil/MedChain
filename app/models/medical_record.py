import uuid
from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from app.database import Base


class MedicalRecordModel(Base):
    __tablename__ = "medical_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, index=True, default=uuid.uuid4
    )
    created_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )
    hash: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    blockchain_tx_id: Mapped[str | None] = mapped_column(String, nullable=True)
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("doctor.public_id")
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("patient.public_id")
    )
    doctor: Mapped["DoctorModel"] = relationship()
    patient: Mapped["PatientModel"] = relationship()

    consultation: Mapped["ConsultationModel"] = relationship(back_populates="medical_record", uselist=False)
    diagnostic: Mapped["DiagnosticModel"] = relationship(back_populates="medical_record", uselist=False)
    certificate: Mapped["MedicalCertificatedModel"] = relationship(back_populates="medical_record", uselist=False)
