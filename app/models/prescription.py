from typing import List
from sqlalchemy import (
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class PrescriptionModel(Base):
    __tablename__ = "prescriptions"

    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    issue_date : Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_at : Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at : Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    consultation_id : Mapped[int] = mapped_column(ForeignKey("consultations.id"))
    consultation: Mapped["ConsultationModel"] = relationship(back_populates="prescription")
    items: Mapped[List["PrescriptionItemModel"]] = relationship(back_populates="prescription")
