from sqlalchemy import (
    String,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class PrescriptionItemModel(Base):

    __tablename__ = "prescription_items"

    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    medication_name : Mapped[str] = mapped_column(String, nullable=False)
    dosage : Mapped[str] = mapped_column(String, nullable=False)
    frequency : Mapped[str] = mapped_column(String, nullable=False)
    treatment_duration : Mapped[str] = mapped_column(String, nullable=False)
    prescription_id : Mapped[int] = mapped_column(ForeignKey("prescriptions.id"))
    prescription: Mapped["PrescriptionModel"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return f"<PrescriptionItem(id={self.id}, medication_name={self.medication_name}, dosage={self.dosage})>"
