import logging
from uuid import UUID
import json
from typing import Optional

from app.models.medical_record import MedicalRecordModel
from app.models.user import UserModel
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.orm import joinedload, selectinload

from app.auth import User, UserRole, get_user
from app.database import get_session
from app.medical_record.enums import MedicalRecordTypes
from app.models.consultation import ConsultationModel
from app.models.diagnostic import DiagnosticModel
from app.models.medical_certificated import MedicalCertificatedModel
from app.models.prescription import PrescriptionModel
from app.models.prescription_item import PrescriptionItemModel
from app.blockchain.solana_client import SolanaHashStorage

logger = logging.getLogger(__name__)


class MedicalRecordsView:
    @staticmethod
    async def get_all(
        type: Optional[MedicalRecordTypes] = None,
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
            stmt_consultation = (
                select(ConsultationModel)
                .options(joinedload(ConsultationModel.medical_record))
                .options(joinedload(ConsultationModel.medical_record.patient))
                .options(joinedload(ConsultationModel.medical_record.doctor))
                .options(joinedload(ConsultationModel.medical_record.doctor.user))
                .options(joinedload(ConsultationModel.medical_record.patient.user))
                .options(
                    selectinload(ConsultationModel.prescription).selectinload(
                        PrescriptionModel.items
                    )
                )
            )

            stmt_diagnostic = (
                select(DiagnosticModel)
                .options(joinedload(DiagnosticModel.medical_record))
                .options(joinedload(DiagnosticModel.medical_record.patient))
                .options(joinedload(DiagnosticModel.medical_record.doctor))
                .options(joinedload(DiagnosticModel.medical_record.doctor.user))
                .options(joinedload(DiagnosticModel.medical_record.patient.user))
            )

            stmt_certificate = (
                select(MedicalCertificatedModel)
                .options(joinedload(MedicalCertificatedModel.medical_record))
                .options(joinedload(MedicalCertificatedModel.medical_record.patient))
                .options(joinedload(MedicalCertificatedModel.medical_record.doctor))
                .options(
                    joinedload(MedicalCertificatedModel.medical_record.doctor.user)
                )
                .options(
                    joinedload(MedicalCertificatedModel.medical_record.patient.user)
                )
            )

            if type == MedicalRecordTypes.CONSULTATION:
                result = await db.execute(stmt_consultation)
                return result.scalars().all()

            elif type == MedicalRecordTypes.DIAGNOSTIC:
                result = await db.execute(stmt_diagnostic)
                return result.scalars().all()

            elif type == MedicalRecordTypes.MEDICAL_CERTIFICATE:
                result = await db.execute(stmt_certificate)
                return result.scalars().all()

            else:
                # Busca todos se nenhum tipo for especificado
                consultations = await db.execute(stmt_consultation)
                diagnostics = await db.execute(stmt_diagnostic)
                certificates = await db.execute(stmt_certificate)

                return {
                    "consultations": consultations.scalars().all(),
                    "diagnostics": diagnostics.scalars().all(),
                    "medical_certificates": certificates.scalars().all(),
                }

        except Exception as e:
            logger.error(f"Erro ao listar prontuarios: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor.",
            )

    async def post(
        self,
        type: MedicalRecordTypes,
        data: dict,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):

        if user not in {
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

        await db.commit()
        await db.refresh(medical_record)

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
                await db.commit()
                await db.refresh(consultation)

                prescription_data = data.get("prescription")
                prescription_items_list = []

                if prescription_data:
                    prescription = PrescriptionModel(consultation_id=consultation.id)
                    db.add(prescription)
                    await db.commit()
                    await db.refresh(prescription)

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
                    await db.commit()

                    # Atualiza o objeto consultation para incluir a relacao recem-criada
                    # Isso garante que o retorno da API inclua a receita
                    await db.refresh(consultation)

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
                    status_code=status.HTTP_400,
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
                await db.commit()
                await db.refresh(diagnostic)

                record_specific_data = {
                    "description": diagnostic.description,
                    "result": diagnostic.result,
                    "issue_date": str(diagnostic.issue_date),
                }

            except Exception as e:
                logger.error(f"Erro ao criar diagnostico: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400,
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
                await db.commit()
                await db.refresh(medical_certificate)

                record_specific_data = {
                    "purpose": medical_certificate.purpose,
                    "period_of_leave": medical_certificate.period_of_leave,
                }

            except Exception as e:
                logger.error(f"Erro ao criar certificado medico: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400,
                    detail="Erro ao criar certificado medico.",
                )

        # --- Integracao com Blockchain ---
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

            # Envia para blockchain (Memo Program)
            tx_id = solana_storage.store_file_hash(str(medical_record.id), file_hash)

            # 3. Atualizar registro com Hash e TxID
            medical_record.hash = file_hash
            medical_record.blockchain_tx_id = (
                tx_id  # Assumindo que o modelo tem este campo
            )
            await db.commit()

        except Exception as e:
            logger.error(f"Erro ao registrar na blockchain: {str(e)}")
            # Nao interrompe o fluxo principal, mas loga o erro (ou poderia lancar excecao dependendo da regra de negocio)

        medical_record_public_id = str(medical_record.public_id)
        if type == MedicalRecordTypes.CONSULTATION:
            return {"medical_record_public_id": medical_record_public_id, "consultation": consultation}
        elif type == MedicalRecordTypes.DIAGNOSTIC:
            return {"medical_record_public_id": medical_record_public_id, "diagnostic": diagnostic}
        elif type == MedicalRecordTypes.MEDICAL_CERTIFICATE:
            return {"medical_record_public_id": medical_record_public_id, "medical_certificate": medical_certificate}

        return {"medical_record_public_id": medical_record_public_id, "message": "Registro criado", "data": record_specific_data}

    async def get_by_public_id(
        self,
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
            result = await db.execute(
                select(MedicalRecordModel)
                .options(joinedload(MedicalRecordModel.patient))
                .options(joinedload(MedicalRecordModel.doctor))
                .options(joinedload(MedicalRecordModel.doctor.user))
                .options(joinedload(MedicalRecordModel.patient.user))
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

            return medical_record

        except Exception as e:
            logger.error(f"Erro ao buscar prontuario por ID: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor.",
            )

    async def get_by_patient_username(
        self,
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
            result = await db.execute(
                select(MedicalRecordModel)
                .options(joinedload(MedicalRecordModel.patient))
                .options(joinedload(MedicalRecordModel.doctor))
                .options(joinedload(MedicalRecordModel.doctor.user))
                .options(joinedload(MedicalRecordModel.patient.user))
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

            return medical_records

        except Exception as e:
            logger.error(
                f"Erro ao buscar prontuarios por nome de usuario do paciente: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor.",
            )
