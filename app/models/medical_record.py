from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class MedicalRecordModel(Base):
    __tablename__ = "medical_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_date: Mapped[datetime] = mapped_column(DateTime)
    updated_date: Mapped[datetime] = mapped_column(DateTime)
    hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctor.public_id"))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient.public_id"))
    doctor: Mapped["DoctorModel"] = relationship()
    patient: Mapped["PatientModel"] = relationship()
