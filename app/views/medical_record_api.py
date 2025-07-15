"""
Rotas API para gerenciamento de registros médicos.
"""
import logging
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from uuid import UUID

from app.database import get_db
from app.service.medical_record_service import MedicalRecordService
from app.models.medical_record import MedicalRecord
from app.dependencies import (
    token_auth, 
    admin_only, 
    user_or_admin,
    verify_record_access,
    verify_patient_records_access,
    verify_doctor_records_access
)
import json

router = APIRouter(tags=["Medical Records"])
logger = logging.getLogger(__name__)

class MedicalRecordCreate(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    description: str
    medications: Optional[List[str]] = []


class MedicalRecordResponse(BaseModel):
    id: int
    patient_id: UUID
    doctor_id: UUID
    description: str
    medications: Optional[List[str]] = []
    date_requested: str
    date_created: str
    blockchain_verified: bool
    blockchain_tx_id: Optional[str] = None
    file_url: Optional[str] = None
    
    class Config:
        orm_mode = True

@router.post("/medical-records/", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_record(
    patient_id: str = Form(...),  # Será convertido para UUID
    doctor_id: str = Form(...),  # Será convertido para UUID
    description: str = Form(...),
    medications: str = Form("[]"),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _: bool = Depends(user_or_admin)
):
    """Cria um novo registro médico com blockchain."""
    try:
        # Converter patient_id para UUID
        try:
            patient_uuid = UUID(patient_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patient_id deve ser um UUID válido"
            )
            
        # Converter doctor_id para UUID
        try:
            doctor_uuid = UUID(doctor_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="doctor_id deve ser um UUID válido"
            )
        
        # Tenta converter medications
        medications_list = []
        if medications:
            try:
                medications_list = json.loads(medications)
                if not isinstance(medications_list, list):
                    raise ValueError("medications deve ser uma lista.")
            except json.JSONDecodeError:
                # Se não for JSON válido, faz split por vírgula
                medications_list = [med.strip() for med in medications.split(",") if med.strip()]
        
        data = {
            "patient_id": patient_uuid,
            "doctor_id": doctor_uuid,
            "description": description,
            "medications": medications_list
        }
        
        service = MedicalRecordService(db)
        record = service.create_medical_record(data, file)
        
        return record
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar registro médico: {str(e)}"
        )

@router.get("/medical-records/{record_id}", response_model=MedicalRecordResponse)
async def get_medical_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_record_access)
):
    """Obtém um registro médico específico."""
    service = MedicalRecordService(db)
    record = service.get_medical_record(record_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro médico não encontrado"
        )
    
    return record

@router.get("/medical-records/", response_model=List[MedicalRecordResponse])
async def list_medical_records(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: bool = Depends(user_or_admin)
):
    """Lista todos os registros médicos."""
    service = MedicalRecordService(db)
    records = service.get_all_medical_records(skip=skip, limit=limit)
    return records

@router.get("/patients/{patient_id}/medical-records", response_model=List[MedicalRecordResponse])
async def get_patient_medical_records(
    patient_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_patient_records_access)
):
    """Obtém todos os registros médicos de um paciente."""
    try:
        patient_uuid = UUID(patient_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="patient_id deve ser um UUID válido"
        )
        
    service = MedicalRecordService(db)
    records = service.get_patient_medical_records(patient_uuid)
    return records

@router.get("/doctors/{doctor_id}/medical-records", response_model=List[MedicalRecordResponse])
async def get_doctor_medical_records(
    doctor_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_doctor_records_access)
):
    """Obtém todos os registros médicos de um médico."""
    try:
        doctor_uuid = UUID(doctor_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="doctor_id deve ser um UUID válido"
        )
        
    service = MedicalRecordService(db)
    records = service.get_doctor_medical_records(doctor_uuid)
    return records
