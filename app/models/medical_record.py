from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime

from app.database import Base


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(PG_UUID, ForeignKey("pacient_records.uid"), nullable=False)
    doctor_id = Column(String(50), index=True, nullable=False)
    description = Column(Text, nullable=False)
    medications = Column(JSONB, nullable=True)
    date_requested = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_updated = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    blockchain_tx_id = Column(String(100), nullable=True)
    blockchain_verified = Column(Boolean, default=False)
    record_hash = Column(String(64), nullable=True)
    file_url = Column(String(255), nullable=True)
    file_hash = Column(String(64), nullable=True)

    # Relacionamento com PacientRecord
    patient = relationship("PacientRecord", back_populates="medical_records")

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "description": self.description,
            "medications": self.medications,
            "date_requested": self.date_requested.isoformat(),
            "date_created": self.date_created.isoformat(),
            "date_updated": self.date_updated.isoformat(),
            "blockchain_tx_id": self.blockchain_tx_id,
            "blockchain_verified": self.blockchain_verified,
            "record_hash": self.record_hash,
            "file_url": self.file_url,
            "file_hash": self.file_hash,
        }

    def sensitive_data(self):
        return {
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "description": self.description,
            "medications": self.medications,
            "date_requested": self.date_requested.isoformat(),
            "file_hash": self.file_hash,
        }
