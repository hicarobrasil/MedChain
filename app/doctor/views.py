from datetime import datetime
from uuid import UUID

from app.database import get_session
from app.doctor.models import DoctorIn
from app.models.doctor import DoctorModel, SpecialtyEnum
from app.models.user import StatusEnum, UserModel
from sqlalchemy.orm import Session as SQLAlchemySession
from fastapi import Depends, HTTPException, status


from app.auth import User, UserRole, get_user


class DoctorView:

    @staticmethod
    async def get_doctor(
        doctor_id: UUID,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não autenticado",
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
        user: User = Depends(get_user),
    ):

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não autenticado",
            )

        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )

        user = UserModel(
            full_name=doctor_data.full_name,
            email=doctor_data.email,
            password=doctor_data.password,
            status=StatusEnum.ACTIVE,
        )

        new_doctor = DoctorModel(
            CRM=doctor_data.CRM,
            specialty=SpecialtyEnum(doctor_data.specialty),
            user=user,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        db.add(new_doctor)
        db.commit()
        db.refresh(new_doctor)

        return 201