from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class DiagnosticModel(Base):
    __tablename__ = "diagnostics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    issue_date: Mapped[str] = mapped_column(DateTime, nullable=False)
    result: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[str] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[str] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    medical_record_id: Mapped[int] = mapped_column(ForeignKey("medical_record.id"))
    medical_record: Mapped["MedicalRecordModel"] = relationship(
        "MedicalRecordModel", back_populates="diagnostic"
    )

    def __repr__(self):
        return f"<DiagnosticModel(id={self.id}, name='{self.name}')>"
