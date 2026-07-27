"""Helpers de autorizacao por vinculo medico-paciente (anti-IDOR)."""
from __future__ import annotations

from typing import Optional, Set
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session as SQLAlchemySession

from app.auth import User, UserRole
from app.models.doctor import DoctorModel
from app.models.doctor_patient import DoctorPatientModel
from app.models.file import FileModel
from app.models.medical_record import MedicalRecordModel
from app.models.patient import PatientModel
from app.models.user import UserModel


def resolve_doctor(db: SQLAlchemySession, user: User) -> Optional[DoctorModel]:
    if not user or not user.email:
        return None
    return (
        db.query(DoctorModel)
        .join(UserModel, DoctorModel.user_id == UserModel.id)
        .filter(UserModel.email == user.email)
        .first()
    )


def resolve_patient_by_uid_or_public_id(
    db: SQLAlchemySession, patient_uid: UUID
) -> Optional[PatientModel]:
    patient = (
        db.query(PatientModel)
        .join(UserModel, PatientModel.user_id == UserModel.id)
        .filter(UserModel.public_id == patient_uid)
        .first()
    )
    if patient:
        return patient
    return db.query(PatientModel).filter(PatientModel.public_id == patient_uid).first()


def linked_patient_public_ids(db: SQLAlchemySession, doctor_public_id: UUID) -> Set[UUID]:
    """Pacientes vinculados via doctor_patient, prontuario ou arquivo."""
    dp_ids = {
        r[0]
        for r in db.query(DoctorPatientModel.patient_id)
        .filter(DoctorPatientModel.doctor_id == doctor_public_id)
        .distinct()
        .all()
        if r[0]
    }
    mr_ids = {
        r[0]
        for r in db.query(MedicalRecordModel.patient_id)
        .filter(MedicalRecordModel.doctor_id == doctor_public_id)
        .distinct()
        .all()
        if r[0]
    }
    file_ids = {
        r[0]
        for r in db.query(FileModel.patient_uid)
        .filter(FileModel.doctor_uid == doctor_public_id)
        .distinct()
        .all()
        if r[0]
    }
    return dp_ids | mr_ids | file_ids


def doctor_has_patient_access(
    db: SQLAlchemySession, doctor_public_id: UUID, patient_public_id: UUID
) -> bool:
    return patient_public_id in linked_patient_public_ids(db, doctor_public_id)


def assert_doctor_owns_doctor_id(
    db: SQLAlchemySession, user: User, doctor_id: UUID, detail: str = "Acesso negado."
) -> DoctorModel:
    """Garante que o medico autenticado so acessa o proprio doctor_id (admin livre)."""
    if user.role == UserRole.ADMIN:
        doctor = db.query(DoctorModel).filter(DoctorModel.public_id == doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medico nao encontrado")
        return doctor

    doctor = resolve_doctor(db, user)
    if not doctor or str(doctor.public_id) != str(doctor_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
    return doctor


def assert_doctor_patient_access(
    db: SQLAlchemySession, user: User, patient_public_id: UUID
) -> None:
    """Admin ok; medico so se vinculado ao paciente."""
    if user.role == UserRole.ADMIN:
        return
    if user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    doctor = resolve_doctor(db, user)
    if not doctor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil de medico nao encontrado.")
    if not doctor_has_patient_access(db, doctor.public_id, patient_public_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a este paciente.")


def ensure_doctor_patient_link(
    db: SQLAlchemySession, doctor_public_id: UUID, patient_public_id: UUID
) -> None:
    """Cria vinculo doctor_patient se ainda nao existir (idempotente)."""
    exists = (
        db.query(DoctorPatientModel)
        .filter(
            DoctorPatientModel.doctor_id == doctor_public_id,
            DoctorPatientModel.patient_id == patient_public_id,
        )
        .first()
    )
    if exists:
        return
    db.add(
        DoctorPatientModel(
            doctor_id=doctor_public_id,
            patient_id=patient_public_id,
        )
    )
    db.commit()
