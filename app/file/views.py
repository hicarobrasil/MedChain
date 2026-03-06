import logging
import os
import uuid
from typing import Optional
from uuid import UUID

from cryptography.fernet import Fernet
from fastapi import UploadFile, File, Depends, HTTPException, status, Form
from sqlalchemy import select
from sqlalchemy.orm import Session as SQLAlchemySession

from app.auth import User, UserRole, get_user
from app.blockchain.solana_client import SolanaHashStorage
from app.database import get_session
from app.models.doctor import DoctorModel
from app.models.file import FileModel
from app.models.user import UserModel

logger = logging.getLogger(__name__)


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
        result_user = await db.execute(stmt_user)
        user_db = result_user.scalar_one_or_none()

        if not user_db:
            raise HTTPException(status_code=401, detail="Usuario nao encontrado.")

        stmt_doctor = select(DoctorModel).where(DoctorModel.user_id == user_db.id)
        result_doctor = await db.execute(stmt_doctor)
        doctor = result_doctor.scalar_one_or_none()

        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas medicos cadastrados podem enviar arquivos.",
            )

        try:
            content = await file.read()

            solana_storage = SolanaHashStorage()
            file_hash = solana_storage.hash_file(content)

            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
            filename = f"{uuid.uuid4()}.{file_ext}"
            file_path = os.path.join(upload_dir, filename)

            # Criptografar o conteudo antes de salvar
            key = os.getenv("MEDICAL_RECORDS_API_CRYPTO_KEY")
            if not key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Chave de criptografia nao configurada.",
                )
            fernet = Fernet(key.encode())
            encrypted_content = fernet.encrypt(content)

            with open(file_path, "wb") as f:
                f.write(encrypted_content)

            doctor_ref = getattr(doctor, "public_id", doctor.id)

            new_file = FileModel(
                url=file_path,
                format=file_type,
                description=description,
                hash=file_hash,
                patient_uid=patient_uid,
                doctor_uid=doctor_ref,
            )

            db.add(new_file)
            await db.commit()
            await db.refresh(new_file)

            try:
                tx_id = solana_storage.store_file_hash(str(new_file.id), file_hash)
                logger.info(f"Arquivo registrado na blockchain. TxID: {tx_id}")
            except Exception as e:
                logger.error(f"Erro ao registrar na blockchain: {e}")

            return {
                "message": "Arquivo enviado com sucesso",
                "id": new_file.id,
                "url": new_file.url,
                "hash": new_file.hash,
            }

        except Exception as e:
            logger.error(f"Erro no upload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao processar o arquivo.",
            )

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

        stmt = select(FileModel).where(FileModel.id == file_id)
        result = await db.execute(stmt)
        file_record = result.scalar_one_or_none()

        if not file_record:
            raise HTTPException(status_code=404, detail="Arquivo nao encontrado.")

        return {
            "id": file_record.id,
            "url": file_record.url,
            "format": file_record.format,
            "description": file_record.description,
            "hash": file_record.hash,
            "patient_uid": file_record.patient_uid,
            "doctor_uid": file_record.doctor_uid,
        }
