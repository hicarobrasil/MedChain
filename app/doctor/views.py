from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session as SQLAlchemySession

from app.auth import User, UserRole, get_user
from app.auth.access import assert_doctor_owns_doctor_id, linked_patient_public_ids
from app.auth.utils import make_password
from app.database import get_session
from app.doctor.schemas import DoctorIn
from app.models.doctor import DoctorModel, SpecialtyEnum
from app.models.user import StatusEnum
from app.models.user import UserModel
from app.models.address import AddressModel
from app.models.doctor_patient import DoctorPatientModel
from app.models.medical_record import MedicalRecordModel
from app.models.consultation import ConsultationModel
from app.models.diagnostic import DiagnosticModel
from app.models.medical_certificated import MedicalCertificatedModel
from app.models.patient import PatientModel


def _serialize_doctor(doctor: DoctorModel) -> dict:
    """Monta o payload no formato de DoctorOut a partir do modelo."""
    return {
        "uid": doctor.public_id,
        "name": doctor.user.full_name,
        "crm": doctor.CRM,
        "specialty": doctor.specialty.value if hasattr(doctor.specialty, "value") else str(doctor.specialty),
        "email": doctor.user.email,
        "phone": "N/A",  # Needs to be added to model if required
        "status": doctor.user.status.value if hasattr(doctor.user.status, "value") else str(doctor.user.status),
        "date_created": doctor.created_date,
        "date_updated": doctor.updated_date,
    }


class DoctorView:

    @staticmethod
    async def list_doctors(
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario nao autenticado")
        doctors = db.query(DoctorModel).join(UserModel, DoctorModel.user_id == UserModel.id).all()
        return [
            {
                "id": str(d.public_id),
                "public_id": str(d.public_id),
                "uid": str(d.public_id),
                "full_name": d.user.full_name,
                "email": d.user.email,
                "CRM": d.CRM,
                "specialty": d.specialty.value if hasattr(d.specialty, "value") else str(d.specialty),
            }
            for d in doctors
        ]

    @staticmethod
    async def get_doctor(
        doctor_id: UUID,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autenticado",
            )

        if user.role not in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.PATIENT]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )

        doctor = (
            db.query(DoctorModel).filter(DoctorModel.public_id == doctor_id).first()
        )
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medico nao encontrado",
            )

        return _serialize_doctor(doctor)

    @staticmethod
    async def create_doctor(
        doctor_data: DoctorIn,
        db: SQLAlchemySession = Depends(get_session),
    ):

        cryptography_password = make_password(doctor_data.password)

        user = UserModel(
            full_name=doctor_data.full_name,
            email=doctor_data.email,
            password=cryptography_password,
            status=StatusEnum.ACTIVE,
        )

        doctor = DoctorModel(
            CRM=doctor_data.CRM,
            specialty=SpecialtyEnum(doctor_data.specialty),
            user=user,
        )

        db.add(user)
        db.add(doctor)
        db.commit()
        db.refresh(doctor)

        return _serialize_doctor(doctor)

    @staticmethod
    async def update_doctor(
        doctor_id: UUID,
        doctor_data: DoctorIn,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autenticado",
            )
        if user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )

        doctor = (
            db.query(DoctorModel).filter(DoctorModel.public_id == doctor_id).first()
        )
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medico nao encontrado",
            )

        doctor.CRM = doctor_data.CRM
        doctor.specialty = SpecialtyEnum(doctor_data.specialty)
        doctor.user.full_name = doctor_data.full_name
        doctor.user.email = doctor_data.email

        if doctor_data.password:
            doctor.user.password = make_password(doctor_data.password)

        db.commit()
        db.refresh(doctor)

        return _serialize_doctor(doctor)

    @staticmethod
    async def get_dashboard_stats(
        doctor_id: UUID,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        """Retorna estatisticas do dashboard do medico: pacientes, prontuarios e consultas."""
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autenticado",
            )
        if user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )

        assert_doctor_owns_doctor_id(db, user, doctor_id)

        records = db.query(MedicalRecordModel).filter(MedicalRecordModel.doctor_id == doctor_id).all()
        record_ids = [r.id for r in records]

        linked_patients = linked_patient_public_ids(db, doctor_id)

        return {
            "patients": len(linked_patients),
            "medical_records": len(records),
            "consultations": db.query(ConsultationModel).filter(
                ConsultationModel.medical_record_id.in_(record_ids)
            ).count() if record_ids else 0,
            "diagnostics": db.query(DiagnosticModel).filter(
                DiagnosticModel.medical_record_id.in_(record_ids)
            ).count() if record_ids else 0,
            "certificates": db.query(MedicalCertificatedModel).filter(
                MedicalCertificatedModel.medical_record_id.in_(record_ids)
            ).count() if record_ids else 0,
        }

    @staticmethod
    async def get_doctor_patients(
        doctor_id: UUID,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        """Retorna pacientes que possuem prontuario com este medico."""
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autenticado",
            )
        if user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )
        if user.role == UserRole.DOCTOR:
            doctor_logged = (
                db.query(DoctorModel)
                .join(UserModel, DoctorModel.user_id == UserModel.id)
                .filter(UserModel.email == user.email)
                .first()
            )
            if not doctor_logged or str(doctor_logged.public_id) != str(doctor_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acesso negado aos pacientes de outro medico",
                )

        doctor = db.query(DoctorModel).filter(DoctorModel.public_id == doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medico nao encontrado",
            )

        # Pacientes vinculados ao medico (doctor_patient ou medical_record para retrocompatibilidade)
        dp_ids = {r[0] for r in db.query(DoctorPatientModel.patient_id).filter(
            DoctorPatientModel.doctor_id == doctor_id
        ).distinct().all() if r[0]}
        mr_ids = {r[0] for r in db.query(MedicalRecordModel.patient_id).filter(
            MedicalRecordModel.doctor_id == doctor_id
        ).distinct().all() if r[0]}
        patient_ids = list(dp_ids | mr_ids)

        if not patient_ids:
            return []

        patients = db.query(PatientModel).join(UserModel, PatientModel.user_id == UserModel.id).filter(
            PatientModel.public_id.in_(patient_ids)
        ).all()

        result = []
        for p in patients:
            address = db.query(AddressModel).filter(AddressModel.patient_id == p.id).first()
            result.append({
                "uid": str(p.user.public_id),
                "id": str(p.user.public_id),
                "patient_public_id": str(p.public_id),
                "name": p.user.full_name,
                "full_name": p.user.full_name,
                "email": p.user.email,
                "phone": p.cellphone,
                "cellphone": p.cellphone,
                "dateofbirth": p.birth_date.isoformat() if p.birth_date else None,
                "birth_date": p.birth_date.isoformat() if p.birth_date else None,
                "gender": p.gender.value if hasattr(p.gender, "value") else str(p.gender),
                "status": p.user.status.value if hasattr(p.user.status, "value") else str(p.user.status),
                "date_created": p.user.created_date,
                "created_at": p.user.created_date,
                "address": {
                    "street": address.street if address else "",
                    "number": address.number if address else "",
                    "complement": address.complement if address else "",
                    "neighborhood": address.neighborhood if address else "",
                    "city": address.city if address else "",
                    "state": address.state if address else "",
                } if address else {},
            })
        return result
