import hashlib
import os
from io import BytesIO
from typing import Tuple

import boto3
from cryptography.fernet import Fernet
from fastapi import UploadFile


class S3Client:
    def __init__(self):
        """Inicializa o cliente S3."""
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("MEDICAL_RECORDS_API_AMAZON_S3_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv(
                "MEDICAL_RECORDS_API_AMAZON_S3_SECRET_ACCESS_KEY"
            ),
        )
        self.bucket_name = os.getenv(
            "MEDICAL_RECORDS_API_AMAZON_S3_MEDICAL_RECORD_FILES_BUCKET_ID"
        )

        # 🔑 chave de criptografia (defina no ambiente)
        key = os.getenv("MEDICAL_RECORDS_API_CRYPTO_KEY")
        if not key:
            raise ValueError(
                "Defina a variavel de ambiente MEDICAL_RECORDS_API_CRYPTO_KEY"
            )
        self.fernet = Fernet(key.encode())

    def upload_file(self, file: UploadFile, key: str) -> Tuple[str, str]:
        """
        Faz upload de um arquivo para o S3 (criptografado).
        """
        content = file.file.read()

        file_hash = hashlib.sha256(content).hexdigest()
        file.file.seek(0)

        encrypted = self.fernet.encrypt(content)

        self.s3.upload_fileobj(BytesIO(encrypted), self.bucket_name, key)

        url = f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
        return url, file_hash

    def download_file(self, key: str) -> UploadFile:
        """
        Baixa um arquivo do S3 e retorna um UploadFile ja descriptografado.
        """
        buffer = BytesIO()
        self.s3.download_fileobj(self.bucket_name, key, buffer)
        buffer.seek(0)

        decrypted = self.fernet.decrypt(buffer.read())

        decrypted_file = UploadFile(
            filename=key,
            file=BytesIO(decrypted),
            content_type="application/octet-stream",
        )
        return decrypted_file

    def criptograph_file(self, file: UploadFile) -> bytes:
        """Retorna conteudo criptografado de um UploadFile."""
        content = file.file.read()
        encrypted = self.fernet.encrypt(content)
        file.file.seek(0)
        return encrypted

    def decriptograph_file(self, file: UploadFile) -> UploadFile:
        """Retorna UploadFile descriptografado a partir de UploadFile criptografado."""
        content = file.file.read()
        decrypted = self.fernet.decrypt(content)
        file.file.seek(0)

        decrypted_file = UploadFile(
            filename=file.filename,
            file=BytesIO(decrypted),
            content_type=file.content_type,
        )
        return decrypted_file
