"""
Serviço de gerenciamento de registros de médicos.
"""
import uuid
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.doctor_record import DoctorRecord, SpecialtyEnum, StatusEnum

class DoctorService:
    def __init__(self, db: Session):
        self.db = db

    def create_doctor(self, data: Dict[str, Any]) -> DoctorRecord:
        """
        Cria um novo registro de médico.
        
        Args:
            data: Dicionário com os dados do médico
            
        Returns:
            Objeto DoctorRecord criado
        """
        try:
            specialty_int = data.get("specialty")
            status_int = data.get("status")

            if specialty_int not in SpecialtyEnum._value2member_map_:
                raise ValueError("Especialidade inválida")
            if status_int not in StatusEnum._value2member_map_:
                raise ValueError("Status inválido")
                
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
            raise HTTPException(status_code=400, detail=f"Erro ao criar médico: {str(e)}")

    def get_doctor_by_uid(self, doctor_uid: uuid.UUID) -> DoctorRecord:
        """
        Busca um médico pelo UID.
        
        Args:
            doctor_uid: UUID do médico
            
        Returns:
            Objeto DoctorRecord encontrado
            
        Raises:
            HTTPException: Se o médico não for encontrado
        """
        doctor = self.db.query(DoctorRecord).filter(DoctorRecord.uid == doctor_uid).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Médico não encontrado")
        return doctor

    def get_doctor_by_crm(self, crm: str) -> DoctorRecord:
        """
        Busca um médico pelo CRM.
        
        Args:
            crm: Número do CRM
            
        Returns:
            Objeto DoctorRecord encontrado
            
        Raises:
            HTTPException: Se o médico não for encontrado
        """
        doctor = self.db.query(DoctorRecord).filter(DoctorRecord.crm == crm).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Médico não encontrado")
        return doctor

    def get_all_doctors(self) -> List[DoctorRecord]:
        """
        Retorna todos os médicos cadastrados.
        
        Returns:
            Lista de objetos DoctorRecord
        """
        return self.db.query(DoctorRecord).all()

    def get_doctors_by_specialty(self, specialty: int) -> List[DoctorRecord]:
        """
        Busca médicos por especialidade.
        
        Args:
            specialty: Código da especialidade (SpecialtyEnum)
            
        Returns:
            Lista de objetos DoctorRecord
        """
        return self.db.query(DoctorRecord).filter(DoctorRecord.specialty == specialty).all()

    def update_doctor(self, doctor_uid: uuid.UUID, update_data: Dict[str, Any]) -> DoctorRecord:
        """
        Atualiza os dados de um médico.
        
        Args:
            doctor_uid: UUID do médico
            update_data: Dicionário com os dados a serem atualizados
            
        Returns:
            Objeto DoctorRecord atualizado
        """
        doctor = self.get_doctor_by_uid(doctor_uid)

        if "specialty" in update_data and update_data["specialty"] is not None:
            specialty_int = update_data["specialty"]
            if specialty_int not in SpecialtyEnum._value2member_map_:
                raise HTTPException(status_code=400, detail="Especialidade inválida")

        if "status" in update_data and update_data["status"] is not None:
            status_int = update_data["status"]
            if status_int not in StatusEnum._value2member_map_:
                raise HTTPException(status_code=400, detail="Status inválido")

        for field, value in update_data.items():
            setattr(doctor, field, value)

        self.db.commit()
        self.db.refresh(doctor)
        return doctor

    def delete_doctor(self, doctor_uid: uuid.UUID):
        """
        Remove um médico do sistema.
        
        Args:
            doctor_uid: UUID do médico
        """
        doctor = self.get_doctor_by_uid(doctor_uid)
        self.db.delete(doctor)
        self.db.commit()

