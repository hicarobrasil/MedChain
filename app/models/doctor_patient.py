"""Modelo de relacionamento médico-paciente (sem prontuário vazio)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DoctorPatientModel(Base):
    """Vincula médico ao paciente para que apareçam na listagem de pacientes do médico."""

    __tablename__ = "doctor_patient"
    __table_args__ = (
        UniqueConstraint("doctor_id", "patient_id", name="uq_doctor_patient"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("doctor.public_id"), nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("patient.public_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    doctor: Mapped["DoctorModel"] = relationship()
    patient: Mapped["PatientModel"] = relationship()
