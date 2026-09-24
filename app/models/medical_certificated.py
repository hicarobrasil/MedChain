from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from app.database import Base


class MedicalCertificatedModel(Base):
    __tablename__ = "medical_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purpose: Mapped[str] = mapped_column(String, nullable=False)
    period_of_leave: Mapped[str] = mapped_column(String, nullable=False)
    created_date: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_date: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    medical_record_id: Mapped[int] = mapped_column(ForeignKey("medical_record.id"))
    medical_record: Mapped["MedicalRecordModel"] = relationship(back_populates="certificate")

    def __repr__(self) -> str:
        return f"<MedicalCertificated(id={self.id}, purpose={self.purpose}, period_of_leave={self.period_of_leave})>"
