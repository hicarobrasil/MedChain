from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base

# Enum baseado em inteiros
class GenderEnum(enum.IntEnum):
    MALE = 0
    FEMALE = 1
    OTHER = 2

class StatusEnum(enum.IntEnum):
    ACTIVE = 0
    INACTIVE = 1
    PENDING = 2

class PacientRecord(Base):
    __tablename__ = "pacient_records"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True, nullable=False)
    dateofbirth = Column(DateTime, nullable=False)
    gender = Column(Integer, nullable=False)
    email = Column(String(100), index=True, nullable=False)
    phone = Column(String(20), index=True, nullable=False)
    status = Column(Integer, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamento com registros médicos
    medical_records = relationship("MedicalRecord", back_populates="patient")

    def get_gender_enum(self) -> GenderEnum:
        return GenderEnum(self.gender)

    def get_status_enum(self) -> StatusEnum:
        return StatusEnum(self.status)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "dateofbirth": self.dateofbirth.isoformat(),
            "gender": self.get_gender_enum().name,
            "email": self.email,
            "phone": self.phone,
            "status": self.get_status_enum().name,
            "date_created": self.date_created.isoformat(),
            "date_updated": self.date_updated.isoformat(),
        }
