from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from database import Base

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), index=True, nullable=False)
    doctor_id = Column(String(50), index=True, nullable=False)
    description = Column(Text, nullable=False)
    medications = Column(JSONB, nullable=True)  # Lista de medicamentos
    date_requested = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Campos relacionados à blockchain
    blockchain_tx_id = Column(String(100), nullable=True)
    blockchain_verified = Column(Boolean, default=False)
    record_hash = Column(String(64), nullable=True)  # Hash SHA-256
    
    # Campos relacionados ao arquivo
    file_url = Column(String(255), nullable=True)
    file_hash = Column(String(64), nullable=True)
    
    def to_dict(self):
        """Converte o registro em um dicionário."""
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
            "file_hash": self.file_hash
        }
        
    def sensitive_data(self):
        """Retorna apenas os dados sensíveis para cálculo do hash."""
        return {
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "description": self.description,
            "medications": self.medications,
            "date_requested": self.date_requested.isoformat(),
            "file_hash": self.file_hash
        }