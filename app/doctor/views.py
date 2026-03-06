from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session as SQLAlchemySession

from app.auth import User, UserRole, get_user
from app.auth.utils import make_password
from app.database import get_session
from app.doctor.schemas import DoctorIn
from app.models.doctor import DoctorModel, SpecialtyEnum
from app.models.user import StatusEnum
from app.models.user import UserModel


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

        return doctor

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
        db.add(user)
        db.commit()
        db.refresh(user)

        doctor = DoctorModel(
            CRM=doctor_data.CRM,
            specialty=SpecialtyEnum(doctor_data.specialty),
            user=user,
        )

        db.add(doctor)
        db.commit()
        db.refresh(doctor)

        return doctor

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

        return doctor
