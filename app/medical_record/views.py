import logging
from uuid import UUID

from app.models.medical_record import MedicalRecordModel
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

logger = logging.getLogger(__name__)


class MedicalRecordsView:
    @staticmethod
    async def get_all_by_type(
        type: MedicalRecordTypes,
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
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado."
            )

        try:
            if type == MedicalRecordTypes.CONSULTATION:
                result = await db.execute(
                    select(ConsultationModel)
                    .options(joinedload(ConsultationModel.medical_record))
                    .options(joinedload(ConsultationModel.medical_record.patient))
                    .options(joinedload(ConsultationModel.medical_record.doctor))
                    .options(joinedload(ConsultationModel.medical_record.doctor.user))
                    .options(joinedload(ConsultationModel.medical_record.patient.user))
                    .options(selectinload(ConsultationModel.prescriptions))
                    .options(selectinload(ConsultationModel.prescriptions.items))
                )
                return result.scalars().all()

            elif type == MedicalRecordTypes.DIAGNOSTIC:
                result = await db.execute(
                    select(DiagnosticModel)
                    .options(joinedload(DiagnosticModel.medical_record))
                    .options(joinedload(DiagnosticModel.medical_record.patient))
                    .options(joinedload(DiagnosticModel.medical_record.doctor))
                    .options(joinedload(DiagnosticModel.medical_record.doctor.user))
                    .options(joinedload(DiagnosticModel.medical_record.patient.user))
                )
                return result.scalars().all()

            elif type == MedicalRecordTypes.MEDICAL_CERTIFICATE:
                result = await db.execute(
                    select(MedicalCertificatedModel)
                    .options(joinedload(MedicalCertificatedModel.medical_record))
                    .options(
                        joinedload(MedicalCertificatedModel.medical_record.patient)
                    )
                    .options(joinedload(MedicalCertificatedModel.medical_record.doctor))
                    .options(
                        joinedload(MedicalCertificatedModel.medical_record.doctor.user)
                    )
                    .options(
                        joinedload(MedicalCertificatedModel.medical_record.patient.user)
                    )
                )
                return result.scalars().all()

        except Exception as e:
            logger.error(f"Erro ao listar prontuários: {str(e)}")
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
            hash=data.get("hash"),
            doctor_id=data.get("doctor_id"),
            patient_id=data.get("patient_id"),
        )

        db.add(medical_record)

        db.commit()
        db.refresh(medical_record)

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

                return consultation

            except Exception as e:
                logger.error(f"Erro ao criar consulta: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400,
                    detail="Erro ao criar consulta.",
                )

        if type == MedicalRecordTypes.DIAGNOSTIC:

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

                return diagnostic

            except Exception as e:
                logger.error(f"Erro ao criar diagnóstico: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400,
                    detail="Erro ao criar diagnóstico.",
                )

        if type == MedicalRecordTypes.MEDICAL_CERTIFICATE:

            try:
                medical_certificate = MedicalCertificatedModel(
                    purpose=data.get("purpose"),
                    period_of_leave=data.get("period_of_leave"),
                    medical_record_id=medical_record.id,
                )
                db.add(medical_certificate)
                db.commit()
                db.refresh(medical_certificate)

                return medical_certificate

            except Exception as e:
                logger.error(f"Erro ao criar certificado médico: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400,
                    detail="Erro ao criar certificado médico.",
                )
                
        
