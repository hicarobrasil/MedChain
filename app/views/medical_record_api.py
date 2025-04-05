"""
Rotas API para gerenciamento de registros médicos.
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.service.medical_record_service import MedicalRecordService
from app.models.medical_record import MedicalRecord

router = APIRouter()

class MedicalRecordCreate(BaseModel):
    patient_id: str
    doctor_id: str
    description: str
    medications: Optional[List[str]] = []

class MedicalRecordResponse(BaseModel):
    id: int
    patient_id: str
    doctor_id: str
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
    patient_id: str = Form(...),
    doctor_id: str = Form(...),
    description: str = Form(...),
    medications: str = Form("[]"),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Cria um novo registro médico com blockchain."""
    try:
        import json
        medications_list = json.loads(medications)
        
        data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
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
async def get_medical_record(record_id: int, db: Session = Depends(get_db)):
    """Busca um registro médico pelo ID."""
    service = MedicalRecordService(db)
    record = service.get_medical_record(record_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro médico com ID {record_id} não encontrado"
        )
        
    return record

@router.get("/medical-records/patient/{patient_id}", response_model=List[MedicalRecordResponse])
async def get_patient_records(patient_id: str, db: Session = Depends(get_db)):
    """Busca todos os registros médicos de um paciente."""
    service = MedicalRecordService(db)
    records = service.get_medical_records_by_patient(patient_id)
    return records

@router.get("/medical-records/doctor/{doctor_id}", response_model=List[MedicalRecordResponse])
async def get_doctor_records(doctor_id: str, db: Session = Depends(get_db)):
    """Busca todos os registros médicos de um médico."""
    service = MedicalRecordService(db)
    records = service.get_medical_records_by_doctor(doctor_id)
    return records

@router.get("/blockchain/status")
async def blockchain_status(db: Session = Depends(get_db)):
    """Verifica o status da conexão com a blockchain."""
    try:
        service = MedicalRecordService(db)
        balance = service.solana_client.check_balance()
        return {
            "status": "connected",
            "balance": balance / 10**9,
            "address": str(service.solana_client.keypair.public_key)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }