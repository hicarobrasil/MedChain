"""
Servico de gerenciamento de registros de medicos.
"""
import uuid
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.doctor import DoctorRecord, SpecialtyEnum, StatusEnum

class DoctorService:
    def __init__(self, db: Session):
        self.db = db

    def create_doctor(self, data: Dict[str, Any]) -> DoctorRecord:
        """
        Cria um novo registro de medico.
        
        Args:
            data: Dicionario com os dados do medico
            
        Returns:
            Objeto DoctorRecord criado
        """
        try:
            specialty_int = data.get("specialty")
            status_int = data.get("status")

            if specialty_int not in SpecialtyEnum._value2member_map_:
                raise ValueError("Especialidade invalida")
            if status_int not in StatusEnum._value2member_map_:
                raise ValueError("Status invalido")
                
            doctor = DoctorRecord(
                name=data.get("name"),
                crm=data.get("crm"),
                specialty=specialty_int,
                email=data.get("email"),
                phone=data.get("phone"),
                status=status_int,
                hospital_affiliation=data.get("hospital_affiliation"),
                office_address=data.get("office_address")
            )

            self.db.add(doctor)
            self.db.commit()
            self.db.refresh(doctor)
           
            return doctor

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Erro ao criar medico: {str(e)}")

    def get_doctor_by_uid(self, doctor_uid: uuid.UUID) -> DoctorRecord:
        """
        Busca um medico pelo UID.
        
        Args:
            doctor_uid: UUID do medico
            
        Returns:
            Objeto DoctorRecord encontrado
            
        Raises:
            HTTPException: Se o medico nao for encontrado
        """
        doctor = self.db.query(DoctorRecord).filter(DoctorRecord.uid == doctor_uid).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Medico nao encontrado")
        return doctor

    def get_doctor_by_crm(self, crm: str) -> DoctorRecord:
        """
        Busca um medico pelo CRM.
        
        Args:
            crm: Numero do CRM
            
        Returns:
            Objeto DoctorRecord encontrado
            
        Raises:
            HTTPException: Se o medico nao for encontrado
        """
        doctor = self.db.query(DoctorRecord).filter(DoctorRecord.crm == crm).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Medico nao encontrado")
        return doctor

    def get_all_doctors(self) -> List[DoctorRecord]:
        """
        Retorna todos os medicos cadastrados.
        
        Returns:
            Lista de objetos DoctorRecord
        """
        return self.db.query(DoctorRecord).all()

    def get_doctors_by_specialty(self, specialty: int) -> List[DoctorRecord]:
        """
        Busca medicos por especialidade.
        
        Args:
            specialty: Codigo da especialidade (SpecialtyEnum)
            
        Returns:
            Lista de objetos DoctorRecord
        """
        return self.db.query(DoctorRecord).filter(DoctorRecord.specialty == specialty).all()

    def update_doctor(self, doctor_uid: uuid.UUID, update_data: Dict[str, Any]) -> DoctorRecord:
        """
        Atualiza os dados de um medico.
        
        Args:
            doctor_uid: UUID do medico
            update_data: Dicionario com os dados a serem atualizados
            
        Returns:
            Objeto DoctorRecord atualizado
        """
        doctor = self.get_doctor_by_uid(doctor_uid)

        if "specialty" in update_data and update_data["specialty"] is not None:
            specialty_int = update_data["specialty"]
            if specialty_int not in SpecialtyEnum._value2member_map_:
                raise HTTPException(status_code=400, detail="Especialidade invalida")

        if "status" in update_data and update_data["status"] is not None:
            status_int = update_data["status"]
            if status_int not in StatusEnum._value2member_map_:
                raise HTTPException(status_code=400, detail="Status invalido")

        for field, value in update_data.items():
            setattr(doctor, field, value)

        self.db.commit()
        self.db.refresh(doctor)
        return doctor

    def delete_doctor(self, doctor_uid: uuid.UUID):
        """
        Remove um medico do sistema.
        
        Args:
            doctor_uid: UUID do medico
        """
        doctor = self.get_doctor_by_uid(doctor_uid)
        self.db.delete(doctor)
        self.db.commit()

