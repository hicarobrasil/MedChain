import os
import pytest
import uuid
from unittest.mock import MagicMock, patch
from app.models.medical_record import MedicalRecordModel
from app.service.medical_record_service import MedicalRecordService
from app.blockchain.solana_client import SolanaHashStorage
from app.storage.aws_client import S3Client

class TestMedicalRecordService:

    @patch.object(SolanaHashStorage, 'store_file_hash')
    @patch.object(SolanaHashStorage, 'hash_file')
    def test_create_medical_record(self, mock_hash_file, mock_store_hash, db_session):
        # Configurar mocks
        mock_hash_file.return_value = "mocked_file_hash_123"
        mock_store_hash.return_value = "mocked_tx_id_456"
        
        # Simular dados de entrada
        doctor_id = uuid.uuid4()
        patient_id = uuid.uuid4()
        data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id
        }
        
        # Criar uma instância do servico
        service = MedicalRecordService(db_session)
        
        # Chamar o metodo de criacao
        record = service.create_medical_record(data)
        
        # Verificacoes
        assert record is not None
        assert record.patient_id == patient_id
        assert record.doctor_id == doctor_id
        assert record.blockchain_tx_id == "mocked_tx_id_456"
        
        # Verificar se os mocks foram chamados corretamente
        mock_hash_file.assert_called_once()
        mock_store_hash.assert_called_once()

    def test_get_medical_record(self, db_session):
        doctor_id = uuid.uuid4()
        patient_id = uuid.uuid4()
        record = MedicalRecordModel(
            doctor_id=doctor_id,
            patient_id=patient_id,
            blockchain_tx_id="tx_123"
        )
        db_session.add(record)
        db_session.commit()
        
        service = MedicalRecordService(db_session)
        fetched_record = service.get_medical_record(record.id)
        
        assert fetched_record is not None
        assert fetched_record.id == record.id
        assert fetched_record.blockchain_tx_id == "tx_123"
