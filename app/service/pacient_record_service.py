"""
Serviço de gerenciamento de registros de pacientes.
"""
from typing import Any, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException


from app.models.pacient_record import PacientRecord, GenderEnum, StatusEnum

class PacientService:

    def __init__(self, db: Session):
        self.db = db

    def create_pacient(self, data: Dict[str, Any]) -> PacientRecord:
        try:
            gender_int = data.get("gender")
            status_int = data.get("status")

            # Verificação se os inteiros são válidos
            if gender_int not in GenderEnum._value2member_map_:
                raise ValueError("Gênero inválido")
            if status_int not in StatusEnum._value2member_map_:
                raise ValueError("Status inválido")
                
            # Salva diretamente como inteiros
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

    def get_pacient_by_id(self, pacient_id: int) -> PacientRecord:
        pacient = self.db.query(PacientRecord).filter(PacientRecord.id == pacient_id).first()
        if not pacient:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")
        return pacient

    def get_all_pacients(self) -> list[PacientRecord]:
        return self.db.query(PacientRecord).all()

    def update_pacient(self, pacient_id: int, update_data: Dict[str, Any]) -> PacientRecord:
        pacient = self.get_pacient_by_id(pacient_id)
        
        # Verifica se gender e status são válidos
        if "gender" in update_data and update_data["gender"] is not None:
            gender_int = update_data["gender"]
            if gender_int not in GenderEnum._value2member_map_:
                raise HTTPException(status_code=400, detail="Gênero inválido")
            # Mantém como inteiro
            
        if "status" in update_data and update_data["status"] is not None:
            status_int = update_data["status"]
            if status_int not in StatusEnum._value2member_map_:
                raise HTTPException(status_code=400, detail="Status inválido")
            # Mantém como inteiro
        
        # Atualiza os campos
        for field, value in update_data.items():
            setattr(pacient, field, value)
            
        self.db.commit()
        self.db.refresh(pacient)
        return pacient

    def delete_pacient(self, pacient_id: int):
        pacient = self.get_pacient_by_id(pacient_id)
        self.db.delete(pacient)
        self.db.commit()