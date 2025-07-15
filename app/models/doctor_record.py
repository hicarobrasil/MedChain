import uuid
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime
import enum

from app.database import Base

class SpecialtyEnum(enum.IntEnum):
    CARDIOLOGY = 0
    DERMATOLOGY = 1
    NEUROLOGY = 2
    PEDIATRICS = 3
    PSYCHIATRY = 4
    ORTHOPEDICS = 5
    GENERAL = 6
    OTHER = 7

class StatusEnum(enum.IntEnum):
    ACTIVE = 0
    INACTIVE = 1
    SUSPENDED = 2

SPECIALTY_MAP = {
    0: "CARDIOLOGY",
    1: "DERMATOLOGY",
    2: "NEUROLOGY",
    3: "PEDIATRICS",
    4: "PSYCHIATRY",
    5: "ORTHOPEDICS",
    6: "GENERAL",
    7: "OTHER"
}

STATUS_MAP = {
    0: "ACTIVE",
    1: "INACTIVE",
    2: "SUSPENDED"
}

SPECIALTY_MAP_REVERSE = {v: k for k, v in SPECIALTY_MAP.items()}
STATUS_MAP_REVERSE = {v: k for k, v in STATUS_MAP.items()}

class DoctorRecord(Base):
    __tablename__ = "doctor_records"

    uid = Column(PG_UUID(as_uuid=True), nullable=False, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), index=True, nullable=False)
    crm = Column(String(20), index=True, unique=True, nullable=False)  # Registro médico
    specialty = Column(Integer, nullable=False)  # SpecialtyEnum
    email = Column(String(100), index=True, nullable=False)
    phone = Column(String(20), index=True, nullable=False)
    status = Column(Integer, nullable=False)  # StatusEnum
    hospital_affiliation = Column(String(200), nullable=True)  # Hospital onde trabalha
    office_address = Column(String(200), nullable=True)  # Endereço do consultório
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relacionamento com registros médicos (comentado temporariamente para testes)
    # medical_records = relationship("MedicalRecord", back_populates="doctor")

    # Propriedades para obter representações em string
    @property
    def specialty_name(self) -> str:
        return SPECIALTY_MAP[self.specialty]

    @property
    def status_name(self) -> str:
        return STATUS_MAP[self.status]

    def get_specialty_enum(self) -> SpecialtyEnum:
        return SpecialtyEnum(self.specialty)

    def get_status_enum(self) -> StatusEnum:
        return StatusEnum(self.status)

    def to_dict(self):
        return {
            "uid": str(self.uid),
            "name": self.name,
            "crm": self.crm,
            "specialty": self.specialty_name,
            "email": self.email,
            "phone": self.phone,
            "status": self.status_name,
            "hospital_affiliation": self.hospital_affiliation,
            "office_address": self.office_address,
            "date_created": self.date_created.isoformat(),
            "date_updated": self.date_updated.isoformat(),
        }

