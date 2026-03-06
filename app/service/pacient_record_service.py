"""
Servico de gerenciamento de registros de pacientes.
"""
import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.patient import PacientRecord, GenderEnum, StatusEnum

class PacientService:

    def __init__(self, db: Session):
        self.db = db

    def create_pacient(self, data: Dict[str, Any]) -> PacientRecord:
        try:
            gender_int = data.get("gender")
            status_int = data.get("status")

            if gender_int not in GenderEnum._value2member_map_:
                raise ValueError("Gênero invalido")
            if status_int not in StatusEnum._value2member_map_:
                raise ValueError("Status invalido")
                
            pacient = PacientRecord(
                name=data.get("name"),
                dateofbirth=data.get("dateofbirth"),
                gender=gender_int, 
                email=data.get("email"),
                phone=data.get("phone"),
                status=status_int, 
            )

            self.db.add(pacient)
            self.db.commit()
            self.db.refresh(pacient)
           
            return pacient

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Erro ao criar paciente: {str(e)}")

    def get_pacient_by_uid(self, pacient_uid: uuid.UUID) -> PacientRecord:
        pacient = self.db.query(PacientRecord).filter(PacientRecord.uid == pacient_uid).first()
        if not pacient:
            raise HTTPException(status_code=404, detail="Paciente nao encontrado")
        return pacient

    def get_all_pacients(self) -> list[PacientRecord]:
        return self.db.query(PacientRecord).all()

    def update_pacient(self, pacient_uid: uuid.UUID, update_data: Dict[str, Any]) -> PacientRecord:
        pacient = self.get_pacient_by_uid(pacient_uid)

        if "gender" in update_data and update_data["gender"] is not None:
            gender_int = update_data["gender"]
            if gender_int not in GenderEnum._value2member_map_:
                raise HTTPException(status_code=400, detail="Gênero invalido")

        if "status" in update_data and update_data["status"] is not None:
            status_int = update_data["status"]
            if status_int not in StatusEnum._value2member_map_:
                raise HTTPException(status_code=400, detail="Status invalido")

        for field, value in update_data.items():
            setattr(pacient, field, value)

        self.db.commit()
        self.db.refresh(pacient)
        return pacient

    def delete_pacient(self, pacient_uid: uuid.UUID):
        pacient = self.get_pacient_by_uid(pacient_uid)
        self.db.delete(pacient)
        self.db.commit()
