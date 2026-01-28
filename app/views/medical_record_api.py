"""
Rotas API para gerenciamento de registros médicos.
"""

import json
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as SQLAlchemySession

from app.auth import UserRole, User, get_user
from app.database import get_session
from app.dependencies import (
    user_or_admin,
    verify_doctor_records_access,
    verify_patient_records_access,
    verify_record_access,
)
from app.models.doctor import DoctorModel
from app.models.patient import PatientModel
from app.models.medical_record import MedicalRecordModel
from app.models.user import UserModel
from sqlalchemy import select, func

from app.service.medical_record_service import MedicalRecordService

router = APIRouter(tags=["Medical Records"])
logger = logging.getLogger(__name__)


class MedicalRecordsResponse(BaseModel):
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


@router.post(
    "/medical-records/",
    response_model=MedicalRecordsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_medical_record(
    patient_id: str = Form(...),  # Será convertido para UUID
    doctor_id: str = Form(...),  # Será convertido para UUID
    description: str = Form(...),
    medications: str = Form("[]"),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _: bool = Depends(user_or_admin),
):
    """Cria um novo registro médico com blockchain."""
    try:
        # Converter patient_id para UUID
        try:
            patient_uuid = UUID(patient_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patient_id deve ser um UUID válido",
            )

        # Converter doctor_id para UUID
        try:
            doctor_uuid = UUID(doctor_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="doctor_id deve ser um UUID válido",
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
                medications_list = [
                    med.strip() for med in medications.split(",") if med.strip()
                ]

        data = {
            "patient_id": patient_uuid,
            "doctor_id": doctor_uuid,
            "description": description,
            "medications": medications_list,
        }

        service = MedicalRecordService(db)
        record = service.create_medical_record(data, file)

        return record

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar registro médico: {str(e)}",
        )


@router.get("/medical-records/{record_id}", response_model=MedicalRecordsResponse)
async def get_medical_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_record_access),
):
    """Obtém um registro médico específico."""
    service = MedicalRecordService(db)
    record = service.get_medical_record(record_id)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro médico não encontrado",
        )

    return record


@router.get("/medical-records/", response_model=List[MedicalRecordsResponse])
async def list_medical_records(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: bool = Depends(user_or_admin),
):
    """Lista todos os registros médicos."""
    service = MedicalRecordService(db)
    records = service.get_all_medical_records(skip=skip, limit=limit)
    return records


@router.get(
    "/patients/{patient_id}/medical-records",
    response_model=List[MedicalRecordsResponse],
)
async def get_patient_medical_records(
    patient_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_patient_records_access),
):
    """Obtém todos os registros médicos de um paciente."""
    try:
        patient_uuid = UUID(patient_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="patient_id deve ser um UUID válido",
        )

    service = MedicalRecordService(db)
    records = service.get_patient_medical_records(patient_uuid)
    return records


@router.get(
    "/doctors/{doctor_id}/medical-records", response_model=List[MedicalRecordsResponse]
)
async def get_doctor_medical_records(
    doctor_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_doctor_records_access),
):
    """Obtém todos os registros médicos de um médico."""
    try:
        doctor_uuid = UUID(doctor_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="doctor_id deve ser um UUID válido",
        )

    service = MedicalRecordService(db)
    records = service.get_doctor_medical_records(doctor_uuid)
    return records


class MedicalRecordsView:
    @staticmethod
    async def get(
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não autenticado.",
            )

        if user.role not in {
            UserRole.ADMIN,
            UserRole.DOCTOR,
            UserRole.PATIENT,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado."
            )

        try:

            medical_records = (
                db.execute(select(MedicalRecordModel).order_by(MedicalRecordModel.id))
                .scalars()
                .all()
            )
            medical_records_response = [
                MedicalRecordsResponse(
                    id=medical_record.id,
                    patient_id=medical_record.patient.user.id_publico,
                    doctor_id=medical_record.doctor.user.id_publico,
                    description=medical_record.description,
                    medications=medical_record.medications,
                    date_requested=medical_record.date_requested.isoformat(),
                    date_created=medical_record.date_created.isoformat(),
                    blockchain_verified=medical_record.blockchain_verified,
                    blockchain_tx_id=medical_record.blockchain_tx_id,
                    file_url=medical_record.file_url,
                )
                for medical_record in medical_records
            ]

            return medical_records_response

        except Exception as e:
            logger.error(f"Erro ao listar prontuários: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor.",
            )
