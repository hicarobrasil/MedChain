from app.database import Base
from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref


class FileModel(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    format: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    prontuario_id: Mapped[int] = mapped_column(ForeignKey("medical_record.id"))
    prontuario: Mapped["MedicalRecordModel"] = relationship()
