from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.doctor import DoctorRecord, StatusEnum, SPECIALTY_MAP_REVERSE, STATUS_MAP_REVERSE
from app.doctor.schemas import DoctorCreate, DoctorUpdate

class DoctorService:
    
    def get_doctor_by_id(self, doctor_id: UUID, db: Session) -> Optional[DoctorRecord]:
        """Busca um médico pelo ID"""
        return db.query(DoctorRecord).filter(DoctorRecord.uid == doctor_id).first()
    
    def get_doctor_by_crm(self, crm: str, db: Session) -> Optional[DoctorRecord]:
        """Busca um médico pelo CRM"""
        return db.query(DoctorRecord).filter(DoctorRecord.crm == crm).first()
    
    def get_doctor_by_email(self, email: str, db: Session) -> Optional[DoctorRecord]:
        """Busca um médico pelo email"""
        return db.query(DoctorRecord).filter(DoctorRecord.email == email).first()
    
    def doctor_exists(self, crm: str, db: Session) -> bool:
        """Verifica se um médico já existe pelo CRM"""
        return self.get_doctor_by_crm(crm, db) is not None
    
    def email_exists(self, email: str, db: Session) -> bool:
        """Verifica se o email já está em uso"""
        return self.get_doctor_by_email(email, db) is not None
    
    def create_doctor(self, doctor_data: DoctorCreate, db: Session) -> DoctorRecord:
        """Cria um novo médico"""
        
        # Converter specialty para int se for string
        specialty_value = doctor_data.specialty
        if isinstance(specialty_value, str):
            specialty_value = SPECIALTY_MAP_REVERSE.get(specialty_value.upper())
            if specialty_value is None:
                raise ValueError(f"Especialidade inválida: {doctor_data.specialty}")
        
        # Converter status para int se for string  
        status_value = doctor_data.status
        if isinstance(status_value, str):
            status_value = STATUS_MAP_REVERSE.get(status_value.upper())
            if status_value is None:
                raise ValueError(f"Status inválido: {doctor_data.status}")
        
        new_doctor = DoctorRecord(
            name=doctor_data.name,
            crm=doctor_data.crm,
            specialty=specialty_value,
            email=doctor_data.email,
            phone=doctor_data.phone,
            status=status_value,
            hospital_affiliation=doctor_data.hospital_affiliation,
            office_address=doctor_data.office_address
        )
        
        db.add(new_doctor)
        db.commit()
        db.refresh(new_doctor)
        
        return new_doctor
    
    def update_doctor(self, doctor: DoctorRecord, doctor_data: DoctorUpdate, db: Session) -> DoctorRecord:
        """Atualiza dados de um médico"""
        
        update_data = doctor_data.dict(exclude_unset=True)
        
        # Converter specialty se fornecido
        if 'specialty' in update_data:
            specialty_value = update_data['specialty']
            if isinstance(specialty_value, str):
                specialty_value = SPECIALTY_MAP_REVERSE.get(specialty_value.upper())
                if specialty_value is None:
                    raise ValueError(f"Especialidade inválida: {update_data['specialty']}")
                update_data['specialty'] = specialty_value
        
        # Converter status se fornecido
        if 'status' in update_data:
            status_value = update_data['status']
            if isinstance(status_value, str):
                status_value = STATUS_MAP_REVERSE.get(status_value.upper())
                if status_value is None:
                    raise ValueError(f"Status inválido: {update_data['status']}")
                update_data['status'] = status_value
        
        for field, value in update_data.items():
            setattr(doctor, field, value)
        
        db.commit()
        db.refresh(doctor)
        
        return doctor
    
    def delete_doctor(self, doctor: DoctorRecord, db: Session) -> bool:
        """Remove um médico do banco"""
        try:
            db.delete(doctor)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
    
    def get_all_doctors(self, skip: int = 0, limit: int = 100, db: Session = None) -> List[DoctorRecord]:
        """Lista todos os médicos com paginação"""
        return db.query(DoctorRecord).offset(skip).limit(limit).all()
    
    def get_doctors_by_specialty(self, specialty: str, db: Session) -> List[DoctorRecord]:
        """Busca médicos por especialidade"""
        specialty_value = SPECIALTY_MAP_REVERSE.get(specialty.upper())
        if specialty_value is None:
            return []
        
        return db.query(DoctorRecord).filter(DoctorRecord.specialty == specialty_value).all()
    
    def get_active_doctors(self, db: Session) -> List[DoctorRecord]:
        """Busca apenas médicos ativos"""
        return db.query(DoctorRecord).filter(DoctorRecord.status == StatusEnum.ACTIVE).all()
