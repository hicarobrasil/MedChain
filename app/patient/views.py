import uuid
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status, Form
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SQLAlchemySession

from app.auth import User, UserRole, get_user
from app.auth.access import (
    assert_doctor_patient_access,
    linked_patient_public_ids,
    resolve_doctor,
    resolve_patient_by_uid_or_public_id,
)
from app.auth.service import UserService
from app.auth.schemas import UserCreateModel
from app.auth.utils import make_password
from app.database import get_session
from app.errors import UserAlreadyExists
from app.models.address import AddressModel
from app.models.doctor import DoctorModel
from app.models.doctor_patient import DoctorPatientModel
from app.models.patient import GenderEnum, PatientModel
from app.models.user import StatusEnum
from app.models.user import UserModel
from app.patient.schemas import PatientRequest


def _serialize_patient(patient: PatientModel, address: Optional[AddressModel] = None) -> dict:
    return {
        "uid": str(patient.user.public_id),
        "id": str(patient.user.public_id),
        "patient_public_id": str(patient.public_id),
        "name": patient.user.full_name,
        "full_name": patient.user.full_name,
        "email": patient.user.email,
        "phone": patient.cellphone,
        "cellphone": patient.cellphone,
        "dateofbirth": patient.birth_date.isoformat() if patient.birth_date else None,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "gender": patient.gender.value if hasattr(patient.gender, "value") else patient.gender,
        "status": patient.user.status.value if hasattr(patient.user.status, "value") else str(patient.user.status),
        "date_created": patient.user.created_date,
        "date_updated": patient.user.updated_date,
        "created_at": patient.user.created_date,
        "address": {
            "uid": str(address.public_id) if address else None,
            "street": address.street if address else "",
            "number": address.number if address else "",
            "complement": address.complement if address else "",
            "neighborhood": address.neighborhood if address else "",
            "city": address.city if address else "",
            "state": address.state if address else "",
        },
    }


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
                detail="Usuario nao autenticado",
            )

        if user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )

        user_svc = UserService()
        if user_svc.user_exists(patient.email, db):
            raise UserAlreadyExists()

        if db.query(PatientModel).filter(PatientModel.cellphone == patient.phone).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Telefone ja cadastrado para outro paciente.",
            )

        try:
            auth_user = user_svc.create_user(
                UserCreateModel(
                    username=patient.email,
                    email=patient.email,
                    password=patient.password,
                ),
                db,
            )
            user_svc.update_user(auth_user, {"role": "patient", "is_verified": True}, db)

            user_created = UserModel(
                full_name=patient.name,
                email=patient.email,
                password=make_password(patient.password),
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
                street=patient.address_street or "",
                number=patient.address_number or "",
                complement=patient.address_complement or "",
                neighborhood=patient.address_neighborhood or "",
                city=patient.address_city or "",
                state=patient.address_state or "",
                patient=create_patient,
            )
            db.add(create_address)
            db.commit()
            db.refresh(create_address)

            # Vincula o paciente ao medico que o criou para aparecer na listagem (sem criar prontuario vazio)
            if user.role == UserRole.DOCTOR:
                doctor = (
                    db.query(DoctorModel)
                    .join(UserModel, DoctorModel.user_id == UserModel.id)
                    .filter(UserModel.email == user.email)
                    .first()
                )
                if doctor:
                    link = DoctorPatientModel(
                        doctor_id=doctor.public_id,
                        patient_id=create_patient.public_id,
                    )
                    db.add(link)
                    db.commit()

            return {
                "uid": str(user_created.public_id),
                "patient_public_id": str(create_patient.public_id),
                "message": "Paciente criado com sucesso",
            }
        except IntegrityError as e:
            db.rollback()
            err_msg = str(e.orig) if e.orig else str(e)
            if "cellphone" in err_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Telefone ja cadastrado para outro paciente.",
                )
            if "email" in err_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="E-mail ja cadastrado.",
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dados duplicados. Verifique e-mail e telefone.",
            )

    @staticmethod
    async def get(
        patient_uid: uuid.UUID,
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

        patient = resolve_patient_by_uid_or_public_id(db, patient_uid)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado"
            )

        assert_doctor_patient_access(db, user, patient.public_id)

        address = db.query(AddressModel).filter(AddressModel.patient_id == patient.id).first()
        return _serialize_patient(patient, address)

    @staticmethod
    async def get_all(
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

        if user.role == UserRole.ADMIN:
            patients = (
                db.query(PatientModel)
                .join(UserModel, PatientModel.user_id == UserModel.id)
                .all()
            )
        else:
            doctor = resolve_doctor(db, user)
            if not doctor:
                return []
            allowed = linked_patient_public_ids(db, doctor.public_id)
            if not allowed:
                return []
            patients = (
                db.query(PatientModel)
                .join(UserModel, PatientModel.user_id == UserModel.id)
                .filter(PatientModel.public_id.in_(allowed))
                .all()
            )

        result = []
        for patient in patients:
            address = db.query(AddressModel).filter(AddressModel.patient_id == patient.id).first()
            result.append(_serialize_patient(patient, address))
        return result

    @staticmethod
    async def put(
        patient_uid: uuid.UUID,
        name: Optional[str] = Form(None),
        email: Optional[str] = Form(None),
        phone: Optional[str] = Form(None),
        dateofbirth: Optional[str] = Form(None),
        gender: Optional[int] = Form(None),
        user_status: Optional[int] = Form(None),
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

        patient = resolve_patient_by_uid_or_public_id(db, patient_uid)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paciente nao encontrado",
            )

        assert_doctor_patient_access(db, user, patient.public_id)

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

        if gender is not None:
            patient.gender = gender
            db.commit()
            db.refresh(patient)

        if user_status is not None:
            patient.user.status = user_status
            db.commit()
            db.refresh(patient.user)

        return {"status": 200, "message": "Paciente atualizado com sucesso"}
