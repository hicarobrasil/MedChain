import os
import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from fastapi import UploadFile
from cryptography.fernet import Fernet
from app.storage.aws_client import S3Client


@pytest.fixture
def mock_env():
    """Mocka as variaveis de ambiente obrigatorias para o S3."""
    key = Fernet.generate_key().decode()
    env_vars = {
        "MEDICAL_RECORDS_API_AMAZON_S3_ACCESS_KEY_ID": "mock_access_key",
        "MEDICAL_RECORDS_API_AMAZON_S3_SECRET_ACCESS_KEY": "mock_secret_key",
        "MEDICAL_RECORDS_API_AMAZON_S3_MEDICAL_RECORD_FILES_BUCKET_ID": "mock_bucket",
        "MEDICAL_RECORDS_API_CRYPTO_KEY": key
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_boto_client():
    """Mocka o boto3.client de forma que possamos ver o que foi chamado."""
    with patch("boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        yield mock_s3


def test_s3client_initialization(mock_env, mock_boto_client):
    """Garante que a classe e o bucket estao sendo lidos do .env corretamente."""
    client = S3Client()
    assert client.bucket_name == "mock_bucket"
    assert client.fernet is not None


def test_s3client_upload_file(mock_env, mock_boto_client):
    """Garante o comportamento de upload pro S3."""
    client = S3Client()
    
    file_content = b"conteudo de teste criptografado"
    upload_file = UploadFile(filename="teste.pdf", file=BytesIO(file_content))
    
    key = "teste_key.pdf"
    url, file_hash = client.upload_file(upload_file, key)
    
    assert url == f"https://mock_bucket.s3.amazonaws.com/{key}"
    assert file_hash is not None
    mock_boto_client.upload_fileobj.assert_called_once()


def test_s3client_download_file(mock_env, mock_boto_client):
    """Garante o comportamento de recebimento e descriptografia."""
    client = S3Client()
    original_content = b"meu conteudo secreto e sensivel"
    encrypted_content = client.fernet.encrypt(original_content)
    
    def mock_download_fileobj(Bucket, Key, Fileobj):
        Fileobj.write(encrypted_content)
    mock_boto_client.download_fileobj.side_effect = mock_download_fileobj
    
    downloaded_upload_file = client.download_file("teste_key.pdf")
    
    assert downloaded_upload_file.filename == "teste_key.pdf"
    assert downloaded_upload_file.file.read() == original_content