"""
Cliente para interação com Amazon S3.
"""
import boto3
import hashlib
import os
from fastapi import UploadFile
from typing import Tuple

class S3Client:
    def __init__(self):
        """Inicializa o cliente S3."""
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AMAZON_S3_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AMAZON_S3_SECRET_ACCESS_KEY')
        )
        self.bucket_name = os.getenv('AMAZON_S3_MEDICAL_RECORD_FILES_BUCKET_ID')
        
    def upload_file(self, file: UploadFile, key: str) -> Tuple[str, str]:
        """
        Faz upload de um arquivo para o S3.
        
        Args:
            file: Arquivo a ser enviado
            key: Caminho/nome do arquivo no S3
            
        Returns:
            Tupla com URL do arquivo e hash SHA-256
        """
        content = file.file.read()
        
        file_hash = hashlib.sha256(content).hexdigest()
        
        file.file.seek(0)
        
        self.s3.upload_fileobj(
            file.file,
            self.bucket_name,
            key
        )
        
        url = f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
        
        return url, file_hash
        
    def get_file_url(self, key: str) -> str:
        """Gera uma URL pré-assinada para download do arquivo."""
        url = self.s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': key
            },
            ExpiresIn=3600
        )
        return url