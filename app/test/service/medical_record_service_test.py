import os
import pytest
from unittest.mock import MagicMock, patch
from app.models.medical_record import MedicalRecord
from app.service.medical_record_service import MedicalRecordService
from app.database import get_db
from app.blockchain.solana_client import SolanaHashStorage
from app.storage.aws_client import S3Client


class MockUploadFile:
    
    def __init__(self, filepath):
        self.filename = os.path.basename(filepath)
        self.file = open(filepath, "rb")
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()


class TestMedicalRecordService:

    @patch.object(S3Client, 'upload_file')
    @patch.object(SolanaHashStorage, 'store_file_hash')
    @patch.object(SolanaHashStorage, 'hash_file')
    def test_create_medical_record(self, mock_hash_file, mock_store_hash, mock_upload_file):
        # Configurar mocks
        mock_hash_file.return_value = "mocked_file_hash_123"
        mock_store_hash.return_value = "mocked_tx_id_456"
        mock_upload_file.return_value = ("https://mock-bucket.s3.amazonaws.com/test_file.txt", "mocked_file_hash_123")
        
        # Obter uma sessão do banco de dados
        db = next(get_db())
        
        # Simular dados de entrada
        data = {
            "patient_id": "12345",
            "doctor_id": "67890", 
            "description": "Consulta de rotina",
            "medications": ["med1", "med2"]
        }
        
        # Caminho para o arquivo de teste
        test_file_path = "arquivo_exemplo.txt"
        
        # Criar o arquivo de teste se não existir
        if not os.path.exists(test_file_path):
            with open(test_file_path, "w") as f:
                f.write("Conteúdo de teste para o arquivo exemplo")
        
        # Simular um arquivo usando MockUploadFile
        with MockUploadFile(test_file_path) as mock_file:
            # Criar uma instância do serviço
            service = MedicalRecordService(db)
            
            # Chamar o método de criação
            record = service.create_medical_record(data, mock_file)
            
            # Verificações
            assert record is not None
            assert record.patient_id == data["patient_id"]
            assert record.doctor_id == data["doctor_id"]
            assert record.description == data["description"]
            assert record.medications == data["medications"]
            assert record.blockchain_verified is True
            assert record.blockchain_tx_id == "mocked_tx_id_456"
            assert record.file_url == "https://mock-bucket.s3.amazonaws.com/test_file.txt"
            assert record.file_hash == "mocked_file_hash_123"
            
            # Verificar se os mocks foram chamados corretamente
            mock_upload_file.assert_called_once()
            mock_hash_file.assert_called_once()
            mock_store_hash.assert_called_once()