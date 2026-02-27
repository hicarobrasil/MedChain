from app.database import Base
from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class FileModel(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    format: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    patient_uid = mapped_column(ForeignKey("patient.public_id"))
    patient: Mapped["PatientModel"] = relationship(back_populates="files")
    doctor_uid: Mapped[int] = mapped_column(ForeignKey("doctor.public_id"))
    doctor: Mapped["DoctorModel"] = relationship(back_populates="files")
