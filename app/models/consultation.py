from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base

class ConsultationModel(Base):

    __tablename__ = "consultations"

    id = Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chief_complaint: Mapped[str] = mapped_column(String, nullable=False)
    history_of_present_illness: Mapped[str] = mapped_column(String, nullable=False)
    diagnosis: Mapped[str] = mapped_column(String, nullable=False)
    treatment_plan: Mapped[str] = mapped_column(String, nullable=False)
    created_date: Mapped[datetime] = mapped_column(DateTime)
    updated_date: Mapped[datetime] = mapped_column(DateTime)
    medical_record_id: Mapped[int] = mapped_column(ForeignKey("medical_record.id"))
    medical_record: Mapped["MedicalRecordModel"] = relationship(back_populates="consultation")

    prescription: Mapped["PrescriptionModel"] = relationship(back_populates="consultation", uselist=False)
    def __repr__(self) -> str:
        return f"<Consultation(id={self.id}, chief_complaint={self.chief_complaint}, diagnosis={self.diagnosis})>"
        return f"<Consultation(id={self.id}, chief_complaint={self.chief_complaint}, diagnosis={self.diagnosis})>"
