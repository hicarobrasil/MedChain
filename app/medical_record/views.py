import logging
from uuid import UUID
import json
from typing import Optional

from app.models.doctor import DoctorModel
from app.models.medical_record import MedicalRecordModel
from app.models.patient import PatientModel
from app.models.user import UserModel
from fastapi import Body, Depends, HTTPException, status
from sqlalchemy import select, true
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.orm import joinedload, selectinload

from app.auth import User, UserRole, get_user
from app.database import get_session
from app.medical_record.enums import MedicalRecordTypes
from app.medical_record.serializers import (
    serialize_consultation,
    serialize_diagnostic,
    serialize_medical_certificate,
    serialize_medical_record_full,
)
from app.models.consultation import ConsultationModel
from app.models.diagnostic import DiagnosticModel
from app.models.medical_certificated import MedicalCertificatedModel
from app.models.prescription import PrescriptionModel
from app.models.prescription_item import PrescriptionItemModel
from app.blockchain.solana_client import SolanaHashStorage
from app.settings import get_settings

logger = logging.getLogger(__name__)


class MedicalRecordsView:
    @staticmethod
    async def get_all(
        type: Optional[MedicalRecordTypes] = None,
        doctor_id: Optional[UUID] = None,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autenticado.",
            )

        if user.role not in {
            UserRole.ADMIN,
            UserRole.DOCTOR,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado."
            )

        try:
            doctor_filter = (
                MedicalRecordModel.doctor_id == doctor_id
                if doctor_id else true()
            )

            stmt_consultation = (
                select(ConsultationModel)
                .join(MedicalRecordModel, ConsultationModel.medical_record_id == MedicalRecordModel.id)
                .where(doctor_filter)
                .options(joinedload(ConsultationModel.medical_record))
                .options(
                    joinedload(ConsultationModel.medical_record)
                    .joinedload(MedicalRecordModel.patient)
                    .joinedload(PatientModel.user)
                )
                .options(
                    joinedload(ConsultationModel.medical_record)
                    .joinedload(MedicalRecordModel.doctor)
                    .joinedload(DoctorModel.user)
                )
                .options(
                    selectinload(ConsultationModel.prescription).selectinload(
                        PrescriptionModel.items
                    )
                )
            )

            stmt_diagnostic = (
                select(DiagnosticModel)
                .join(MedicalRecordModel, DiagnosticModel.medical_record_id == MedicalRecordModel.id)
                .where(doctor_filter)
                .options(joinedload(DiagnosticModel.medical_record))
                .options(
                    joinedload(DiagnosticModel.medical_record)
                    .joinedload(MedicalRecordModel.patient)
                    .joinedload(PatientModel.user)
                )
                .options(
                    joinedload(DiagnosticModel.medical_record)
                    .joinedload(MedicalRecordModel.doctor)
                    .joinedload(DoctorModel.user)
                )
            )

            stmt_certificate = (
                select(MedicalCertificatedModel)
                .join(MedicalRecordModel, MedicalCertificatedModel.medical_record_id == MedicalRecordModel.id)
                .where(doctor_filter)
                .options(joinedload(MedicalCertificatedModel.medical_record))
                .options(
                    joinedload(MedicalCertificatedModel.medical_record)
                    .joinedload(MedicalRecordModel.patient)
                    .joinedload(PatientModel.user)
                )
                .options(
                    joinedload(MedicalCertificatedModel.medical_record)
                    .joinedload(MedicalRecordModel.doctor)
                    .joinedload(DoctorModel.user)
                )
            )

            if type == MedicalRecordTypes.CONSULTATION:
                result = db.execute(stmt_consultation)
                items = result.scalars().all()
                return [serialize_consultation(c) for c in items]

            elif type == MedicalRecordTypes.DIAGNOSTIC:
                result = db.execute(stmt_diagnostic)
                items = result.scalars().all()
                return [serialize_diagnostic(d) for d in items]

            elif type == MedicalRecordTypes.MEDICAL_CERTIFICATE:
                result = db.execute(stmt_certificate)
                items = result.scalars().all()
                return [serialize_medical_certificate(c) for c in items]

            else:
                # Busca todos se nenhum tipo for especificado
                consultations = db.execute(stmt_consultation).scalars().all()
                diagnostics = db.execute(stmt_diagnostic).scalars().all()
                certificates = db.execute(stmt_certificate).scalars().all()

                return {
                    "consultations": [serialize_consultation(c) for c in consultations],
                    "diagnostics": [serialize_diagnostic(d) for d in diagnostics],
                    "medical_certificates": [serialize_medical_certificate(c) for c in certificates],
                }

        except Exception as e:
            logger.error(f"Erro ao listar prontuarios: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor.",
            )

    @staticmethod
    async def post(
        payload: dict = Body(...),
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        type = MedicalRecordTypes(payload.get("type", "consultation"))
        data = payload.get("data", {})

        if user.role not in {
            UserRole.ADMIN,
            UserRole.DOCTOR,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado."
            )

        medical_record = MedicalRecordModel(
            doctor_id=data.get("doctor_id"),
            patient_id=data.get("patient_id"),
        )

        db.add(medical_record)

        db.commit()
        db.refresh(medical_record)

        record_specific_data = {}

        if type == MedicalRecordTypes.CONSULTATION:

            try:

                consultation = ConsultationModel(
                    chief_complaint=data.get("chief_complaint"),
                    history_of_present_illness=data.get("history_of_present_illness"),
                    diagnosis=data.get("diagnosis"),
                    treatment_plan=data.get("treatment_plan"),
                    medical_record_id=medical_record.id,
                )

                db.add(consultation)
                db.commit()
                db.refresh(consultation)

                prescription_data = data.get("prescription")
                prescription_items_list = []

                if prescription_data:
                    prescription = PrescriptionModel(consultation_id=consultation.id)
                    db.add(prescription)
                    db.commit()
                    db.refresh(prescription)

                    items = prescription_data.get("items", [])
                    for item in items:
                        prescription_item = PrescriptionItemModel(
                            medication_name=item.get("medication_name"),
                            dosage=item.get("dosage"),
                            frequency=item.get("frequency"),
                            treatment_duration=item.get("treatment_duration"),
                            prescription_id=prescription.id,
                        )
                        db.add(prescription_item)
                        prescription_items_list.append(
                            {
                                "medication_name": item.get("medication_name"),
                                "dosage": item.get("dosage"),
                                "frequency": item.get("frequency"),
                                "treatment_duration": item.get("treatment_duration"),
                            }
                        )
                    db.commit()

                    # Atualiza o objeto consultation para incluir a relacao recem-criada
                    # Isso garante que o retorno da API inclua a receita
                    db.refresh(consultation)

                record_specific_data = {
                    "chief_complaint": consultation.chief_complaint,
                    "diagnosis": consultation.diagnosis,
                    "treatment_plan": consultation.treatment_plan,
                    "prescription": (
                        prescription_items_list if prescription_data else None
                    ),
                }

            except Exception as e:
                logger.error(f"Erro ao criar consulta: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Erro ao criar consulta.",
                )

        elif type == MedicalRecordTypes.DIAGNOSTIC:

            try:
                diagnostic = DiagnosticModel(
                    description=data.get("description"),
                    issue_date=data.get("issue_date"),
                    result=data.get("result"),
                    medical_record_id=medical_record.id,
                )
                db.add(diagnostic)
                db.commit()
                db.refresh(diagnostic)

                record_specific_data = {
                    "description": diagnostic.description,
                    "result": diagnostic.result,
                    "issue_date": str(diagnostic.issue_date),
                }

            except Exception as e:
                logger.error(f"Erro ao criar diagnostico: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Erro ao criar diagnostico.",
                )

        elif type == MedicalRecordTypes.MEDICAL_CERTIFICATE:

            try:
                medical_certificate = MedicalCertificatedModel(
                    purpose=data.get("purpose"),
                    period_of_leave=data.get("period_of_leave"),
                    medical_record_id=medical_record.id,
                )
                db.add(medical_certificate)
                db.commit()
                db.refresh(medical_certificate)

                record_specific_data = {
                    "purpose": medical_certificate.purpose,
                    "period_of_leave": medical_certificate.period_of_leave,
                }

            except Exception as e:
                logger.error(f"Erro ao criar certificado medico: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Erro ao criar certificado medico.",
                )

        # --- Integracao com Blockchain ---
        settings = get_settings()
        if settings.ENABLE_BLOCKCHAIN:
            try:
                # 1. Preparar dados para hash (Metadados + Dados Especificos)
                payload_to_hash = {
                    "record_id": str(medical_record.id),
                    "patient_id": str(medical_record.patient_id),
                    "doctor_id": str(medical_record.doctor_id),
                    "type": type.value,
                    "data": record_specific_data,
                }

                # Serializa garantindo ordem das chaves para reprodutibilidade do hash
                payload_bytes = json.dumps(payload_to_hash, sort_keys=True).encode("utf-8")

                # 2. Calcular Hash e Enviar para Solana
                solana_storage = SolanaHashStorage()
                file_hash = solana_storage.hash_file(payload_bytes)

                # Tentar airdrop se saldo zerado (devnet)
                try:
                    if solana_storage.get_balance() < 0.01:
                        solana_storage.airdrop(1.0)
                except Exception as airdrop_err:
                    logger.warning(f"Airdrop Solana falhou: {airdrop_err}")

                # Envia para blockchain (Memo Program)
                tx_id = solana_storage.store_file_hash(str(medical_record.id), file_hash)

                if tx_id:
                    medical_record.hash = file_hash
                    medical_record.blockchain_tx_id = tx_id
                    db.commit()
            except Exception as e:
                logger.error(f"Erro ao registrar na blockchain: {str(e)}")

        medical_record_public_id = str(medical_record.public_id)
        if type == MedicalRecordTypes.CONSULTATION:
            return {"medical_record_public_id": medical_record_public_id, "consultation": record_specific_data}
        elif type == MedicalRecordTypes.DIAGNOSTIC:
            return {"medical_record_public_id": medical_record_public_id, "diagnostic": record_specific_data}
        elif type == MedicalRecordTypes.MEDICAL_CERTIFICATE:
            return {"medical_record_public_id": medical_record_public_id, "medical_certificate": record_specific_data}

        return {"medical_record_public_id": medical_record_public_id, "message": "Registro criado", "data": record_specific_data}

    @staticmethod
    async def get_by_public_id(
        public_id: UUID,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autenticado.",
            )

        if user.role not in {
            UserRole.ADMIN,
            UserRole.DOCTOR,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado."
            )

        try:
            result = db.execute(
                select(MedicalRecordModel)
                .options(
                    joinedload(MedicalRecordModel.patient).joinedload(PatientModel.user)
                )
                .options(
                    joinedload(MedicalRecordModel.doctor).joinedload(DoctorModel.user)
                )
                .options(selectinload(MedicalRecordModel.consultation))
                .options(selectinload(MedicalRecordModel.diagnostic))
                .options(selectinload(MedicalRecordModel.certificate))
                .options(
                    selectinload(MedicalRecordModel.consultation)
                    .selectinload(ConsultationModel.prescription)
                    .selectinload(PrescriptionModel.items)
                )
                .where(MedicalRecordModel.public_id == public_id)
            )
            medical_record = result.scalar_one_or_none()

            if not medical_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Prontuario nao encontrado.",
                )

            return serialize_medical_record_full(medical_record)

        except Exception as e:
            logger.error(f"Erro ao buscar prontuario por ID: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor.",
            )

    @staticmethod
    async def get_by_patient_username(
        username: str,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autenticado.",
            )

        if user.role not in {
            UserRole.ADMIN,
            UserRole.DOCTOR,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado."
            )

        try:
            result = db.execute(
                select(MedicalRecordModel)
                .options(
                    joinedload(MedicalRecordModel.patient).joinedload(PatientModel.user)
                )
                .options(
                    joinedload(MedicalRecordModel.doctor).joinedload(DoctorModel.user)
                )
                .options(selectinload(MedicalRecordModel.consultation))
                .options(selectinload(MedicalRecordModel.diagnostic))
                .options(selectinload(MedicalRecordModel.certificate))
                .options(
                    selectinload(MedicalRecordModel.consultation)
                    .selectinload(ConsultationModel.prescription)
                    .selectinload(PrescriptionModel.items)
                )
                .where(MedicalRecordModel.patient.has(UserModel.username == username))
            )
            medical_records = result.scalars().all()

            return [serialize_medical_record_full(mr) for mr in medical_records]

        except Exception as e:
            logger.error(
                f"Erro ao buscar prontuarios por nome de usuario do paciente: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor.",
            )
