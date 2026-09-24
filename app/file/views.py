import base64
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from fastapi import UploadFile, File, Depends, HTTPException, status, Form
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SQLAlchemySession

from app.auth import User, UserRole, get_user
from app.auth.access import (
    assert_doctor_patient_access,
    doctor_has_patient_access,
    resolve_doctor,
    resolve_patient_by_uid_or_public_id,
)
from app.blockchain.solana_client import SolanaHashStorage
from app.database import get_session
from app.models.doctor import DoctorModel
from app.models.file import FileModel
from app.models.patient import PatientModel
from app.models.user import UserModel
from app.settings import get_settings

logger = logging.getLogger(__name__)


def _safe_unlink(path: Optional[str]) -> None:
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        logger.warning("Falha ao remover arquivo temporario %s: %s", path, exc)


def _serialize_file(file_record: FileModel) -> dict:
    tx_id = getattr(file_record, "blockchain_tx_id", None)
    return {
        "id": file_record.id,
        "url": file_record.url,
        "format": file_record.format,
        "description": file_record.description,
        "hash": file_record.hash,
        "blockchain_tx_id": tx_id,
        "anchored": bool(file_record.hash and tx_id),
        "created_date": (
            file_record.created_date.isoformat()
            if getattr(file_record, "created_date", None)
            else None
        ),
        "patient_uid": str(file_record.patient_uid),
        "doctor_uid": str(file_record.doctor_uid),
    }


def _get_fernet() -> Fernet:
    key = get_settings().MEDICAL_RECORDS_API_CRYPTO_KEY or os.getenv(
        "MEDICAL_RECORDS_API_CRYPTO_KEY"
    )
    if not key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chave de criptografia nao configurada.",
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def _resolve_patient_public_id(db: SQLAlchemySession, user: User) -> Optional[UUID]:
    user_db = db.execute(
        select(UserModel).where(UserModel.email == user.email)
    ).scalar_one_or_none()
    if not user_db:
        return None
    patient = db.execute(
        select(PatientModel).where(PatientModel.user_id == user_db.id)
    ).scalar_one_or_none()
    return patient.public_id if patient else None


def _assert_file_access(db: SQLAlchemySession, user: User, file_record: FileModel) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.DOCTOR:
        doctor = resolve_doctor(db, user)
        if doctor and str(doctor.public_id) == str(file_record.doctor_uid):
            return
        if doctor and doctor_has_patient_access(db, doctor.public_id, file_record.patient_uid):
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    if user.role == UserRole.PATIENT:
        patient_id = _resolve_patient_public_id(db, user)
        if patient_id and str(patient_id) == str(file_record.patient_uid):
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")


def _read_decrypted_file(file_record: FileModel) -> bytes:
    path = file_record.url
    if not path or not os.path.isfile(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conteudo do arquivo nao encontrado no servidor.",
        )
    try:
        with open(path, "rb") as f:
            encrypted = f.read()
        return _get_fernet().decrypt(encrypted)
    except InvalidToken:
        logger.error("Falha ao descriptografar arquivo id=%s", file_record.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel descriptografar o arquivo.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao ler arquivo id=%s: %s", file_record.id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao ler o arquivo.",
        )


def _download_filename(file_record: FileModel) -> str:
    ext_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "application/pdf": "pdf",
    }
    ext = ext_map.get(file_record.format, "bin")
    base = (file_record.description or f"arquivo-{file_record.id}").strip()
    safe = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in base).strip() or f"arquivo-{file_record.id}"
    if not safe.lower().endswith(f".{ext}"):
        safe = f"{safe}.{ext}"
    return safe


class FileView:
    @staticmethod
    async def upload_file(
        patient_uid: UUID = Form(...),
        file: UploadFile = File(...),
        description: Optional[str] = Form(None),
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autenticado.",
            )

        if user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permissao negada."
            )

        file_type = file.content_type
        if file_type not in [
            "image/jpeg",
            "image/png",
            "application/pdf",
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de arquivo nao suportado. Apenas JPEG, PNG e PDF sao permitidos.",
            )

        stmt_user = select(UserModel).where(UserModel.email == user.email)
        user_db = db.execute(stmt_user).scalar_one_or_none()

        if not user_db:
            raise HTTPException(status_code=401, detail="Usuario nao encontrado.")

        stmt_doctor = select(DoctorModel).where(DoctorModel.user_id == user_db.id)
        doctor = db.execute(stmt_doctor).scalar_one_or_none()

        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas medicos cadastrados podem enviar arquivos.",
            )

        patient = resolve_patient_by_uid_or_public_id(db, patient_uid)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paciente nao encontrado.",
            )
        patient_uid = patient.public_id

        if user.role == UserRole.DOCTOR and not doctor_has_patient_access(
            db, doctor.public_id, patient_uid
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado a este paciente.",
            )

        file_path = None
        try:
            content = await file.read()
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Arquivo vazio nao permitido.",
                )

            solana_storage = SolanaHashStorage()
            file_hash = solana_storage.hash_file(content)

            # Unique em files.hash: falha previsível com 409 (não 500).
            existing = db.execute(
                select(FileModel.id).where(FileModel.hash == file_hash).limit(1)
            ).scalar_one_or_none()
            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Este arquivo ja foi enviado anteriormente "
                        "(conteudo identico detectado pelo hash)."
                    ),
                )

            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_ext = (
                file.filename.split(".")[-1]
                if file.filename and "." in file.filename
                else "bin"
            )
            filename = f"{uuid.uuid4()}.{file_ext}"
            file_path = os.path.join(upload_dir, filename)

            fernet = _get_fernet()
            encrypted_content = fernet.encrypt(content)

            with open(file_path, "wb") as f:
                f.write(encrypted_content)

            doctor_ref = getattr(doctor, "public_id", doctor.id)
            desc = description or (file.filename if file.filename else None)

            new_file = FileModel(
                url=file_path,
                format=file_type,
                description=desc,
                hash=file_hash,
                created_date=datetime.now(timezone.utc),
                patient_uid=patient_uid,
                doctor_uid=doctor_ref,
            )

            try:
                db.add(new_file)
                db.commit()
                db.refresh(new_file)
            except IntegrityError:
                db.rollback()
                _safe_unlink(file_path)
                file_path = None
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Este arquivo ja foi enviado anteriormente "
                        "(conteudo identico detectado pelo hash)."
                    ),
                )

            try:
                tx_id = solana_storage.store_file_hash(str(new_file.id), file_hash)
                new_file.blockchain_tx_id = tx_id
                db.commit()
                db.refresh(new_file)
                logger.info(f"Arquivo registrado na blockchain. TxID: {tx_id}")
            except Exception as e:
                logger.error(f"Erro ao registrar na blockchain: {e}")

            return {
                "message": "Arquivo enviado com sucesso",
                **_serialize_file(new_file),
            }

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            _safe_unlink(file_path)
            logger.error(f"Erro no upload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao processar o arquivo.",
            )

    @staticmethod
    async def list_by_patient(
        patient_uid: UUID,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autenticado.",
            )

        if user.role not in [UserRole.DOCTOR, UserRole.ADMIN, UserRole.PATIENT]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permissao negada."
            )

        if user.role == UserRole.PATIENT:
            patient_id = _resolve_patient_public_id(db, user)
            if not patient_id or str(patient_id) != str(patient_uid):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado."
                )
        elif user.role == UserRole.DOCTOR:
            patient = resolve_patient_by_uid_or_public_id(db, patient_uid)
            if not patient:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
                )
            assert_doctor_patient_access(db, user, patient.public_id)
            patient_uid = patient.public_id

        files = db.execute(
            select(FileModel).where(FileModel.patient_uid == patient_uid)
        ).scalars().all()

        return [_serialize_file(f) for f in files]

    @staticmethod
    async def get_file(
        file_id: int,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autenticado.",
            )

        file_record = db.execute(
            select(FileModel).where(FileModel.id == file_id)
        ).scalar_one_or_none()

        if not file_record:
            raise HTTPException(status_code=404, detail="Arquivo nao encontrado.")

        _assert_file_access(db, user, file_record)

        return _serialize_file(file_record)

    @staticmethod
    async def download_file(
        file_id: int,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        """Retorna o conteudo descriptografado para visualizacao/download."""
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autenticado.",
            )

        if user.role not in [UserRole.DOCTOR, UserRole.ADMIN, UserRole.PATIENT]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permissao negada."
            )

        file_record = db.execute(
            select(FileModel).where(FileModel.id == file_id)
        ).scalar_one_or_none()

        if not file_record:
            raise HTTPException(status_code=404, detail="Arquivo nao encontrado.")

        _assert_file_access(db, user, file_record)
        content = _read_decrypted_file(file_record)
        filename = _download_filename(file_record)

        return Response(
            content=content,
            media_type=file_record.format or "application/octet-stream",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control": "private, no-store",
            },
        )

    @staticmethod
    async def get_all_files_by_patient(
        patient_uid: UUID,
        db: SQLAlchemySession = Depends(get_session),
        user: User = Depends(get_user),
    ):
        """Lista os arquivos do paciente ja com o conteudo descriptografado em base64."""
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao autenticado.",
            )

        if user.role not in [UserRole.DOCTOR, UserRole.ADMIN, UserRole.PATIENT]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permissao negada."
            )

        if user.role == UserRole.PATIENT:
            patient_id = _resolve_patient_public_id(db, user)
            if not patient_id or str(patient_id) != str(patient_uid):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado."
                )
        elif user.role == UserRole.DOCTOR:
            patient = resolve_patient_by_uid_or_public_id(db, patient_uid)
            if not patient:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado."
                )
            assert_doctor_patient_access(db, user, patient.public_id)
            patient_uid = patient.public_id

        files = db.execute(
            select(FileModel).where(FileModel.patient_uid == patient_uid)
        ).scalars().all()

        response = []
        for file_record in files:
            try:
                content = base64.b64encode(_read_decrypted_file(file_record)).decode("utf-8")
            except HTTPException as exc:
                logger.error(
                    "Erro ao descriptografar arquivo %s: %s", file_record.id, exc.detail
                )
                content = None
            response.append({**_serialize_file(file_record), "content": content})

        return response
