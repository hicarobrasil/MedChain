import uuid
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session as SQLAlchemySession

from app.auth import User, UserRole, get_user
from app.auth.utils import make_password
from app.database import get_session
from app.models.address import AddressModel
from app.models.patient import GenderEnum, PatientModel
from app.models.user import StatusEnum
from app.models.user import UserModel
from app.patient.schemas import PatientRequest


class PatientView:

    @staticmethod
    async def post(
        patient: PatientRequest,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não autenticado",
            )

        if user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )

        user_created = UserModel(
            full_name=patient.name,
            email=patient.email,
            password=make_password(patient.phone),
            status=StatusEnum.ACTIVE,
        )
        db.add(user_created)
        db.commit()
        db.refresh(user_created)

        create_patient = PatientModel(
            cellphone=patient.phone,
            birth_date=patient.dateofbirth,
            gender=GenderEnum(patient.gender),
            user=user_created,
        )
        db.add(create_patient)
        db.commit()
        db.refresh(create_patient)

        create_address = AddressModel(
            street=make_password(patient.address_street),
            number=make_password(patient.address_number),
            complement=make_password(patient.address_complement),
            neighborhood=make_password(patient.address_neighborhood),
            city=make_password(patient.address_city),
            state=make_password(patient.address_state),
            patient=create_patient,
        )

        db.add(create_address)
        db.commit()
        db.refresh(create_address)

        return {"uid": user_created.public_id, "message": "Paciente criado com sucesso"}

    @staticmethod
    async def get(
        patient_uid: uuid.UUID,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não autenticado",
            )

        if user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )

        patient = (
            db.query(PatientModel)
            .join(UserModel, PatientModel.user_id == UserModel.id)
            .filter(UserModel.public_id == patient_uid)
            .first()
        )

        address = (
            db.query(AddressModel).filter(AddressModel.patient_id == patient.id).first()
        )

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Paciente não encontrado"
            )
        return {
            "uid": patient.user.public_id,
            "name": patient.user.full_name,
            "email": patient.user.email,
            "phone": patient.cellphone,
            "dateofbirth": patient.birth_date,
            "gender": patient.gender,
            "status": patient.user.status,
            "date_created": patient.user.created_date,
            "date_updated": patient.user.updated_date,
            "address": {
                "uid": address.public_id,
                "street": address.street,
                "number": address.number,
                "complement": address.complement,
                "neighborhood": address.neighborhood,
                "city": address.city,
                "state": address.state,
            },
        }, 200

    @staticmethod
    async def get_all(
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não autenticado",
            )

        if user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )

        patients = db.join(UserModel, PatientModel.user_id == UserModel.id).all(
            PatientModel
        )
        return [
            {
                "uid": patient.user.public_id,
                "name": patient.user.full_name,
                "email": patient.user.email,
                "phone": patient.cellphone,
                "dateofbirth": patient.birth,
                "gender": patient.gender,
                "status": patient.status,
            }
            for patient in patients
        ], 200

    @staticmethod
    async def put(
        patient_uid: uuid.UUID,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        dateofbirth: Optional[datetime] = None,
        gender: Optional[int] = None,
        user_status: Optional[int] = None,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não autenticado",
            )

        if user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )

        patient = (
            db.query(PatientModel)
            .join(UserModel, PatientModel.user_id == UserModel.id)
            .filter(UserModel.public_id == patient_uid)
            .first()
        )

        if not patient:
            raise HTTPException(
                "Paciente não encontrado", status_code=status.HTTP_404_NOT_FOUND
            )

        if name:
            patient.user.full_name = name

            db.commit()
            db.refresh(patient.user)

        if email:
            patient.user.email = email

            db.commit()
            db.refresh(patient.user)

        if phone:
            patient.cellphone = phone

            db.commit()
            db.refresh(patient)

        if dateofbirth:
            patient.birth_date = dateofbirth

            db.commit()
            db.refresh(patient)

        if gender:
            patient.gender = gender

            db.commit()
            db.refresh(patient)

        if user_status:
            patient.user.status = user_status

            db.commit()
            db.refresh(patient.user)

    return {"status": 200, "message": "Paciente atualizado com sucesso"}
