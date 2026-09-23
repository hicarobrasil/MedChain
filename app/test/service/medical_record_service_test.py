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

    @patch.object(SolanaHashStorage, 'store_file_hash')
    @patch.object(SolanaHashStorage, 'hash_file')
    def test_create_medical_record_exception_handling(self, mock_hash_file, mock_store_hash, db_session):
        # Configurar mock para falhar na blockchain
        mock_hash_file.return_value = "mocked_file_hash_123"
        mock_store_hash.side_effect = Exception("Blockchain failure")
        
        doctor_id = uuid.uuid4()
        patient_id = uuid.uuid4()
        data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id
        }
        
        service = MedicalRecordService(db_session)
        # Deve executar sem levantar exceção, pois o erro é tratado internamente
        record = service.create_medical_record(data)
        
        assert record.blockchain_tx_id is None
        mock_store_hash.assert_called_once()

    def test_get_medical_records_by_patient(self, db_session):
        patient_id = uuid.uuid4()
        record1 = MedicalRecordModel(doctor_id=uuid.uuid4(), patient_id=patient_id)
        record2 = MedicalRecordModel(doctor_id=uuid.uuid4(), patient_id=uuid.uuid4())
        db_session.add_all([record1, record2])
        db_session.commit()
        
        service = MedicalRecordService(db_session)
        records = service.get_medical_records_by_patient(patient_id)
        
        assert len(records) == 1
        assert records[0].patient_id == patient_id

    def test_get_medical_records_by_doctor(self, db_session):
        doctor_id = uuid.uuid4()
        record1 = MedicalRecordModel(doctor_id=doctor_id, patient_id=uuid.uuid4())
        record2 = MedicalRecordModel(doctor_id=uuid.uuid4(), patient_id=uuid.uuid4())
        db_session.add_all([record1, record2])
        db_session.commit()
        
        service = MedicalRecordService(db_session)
        records = service.get_medical_records_by_doctor(doctor_id)
        
        assert len(records) == 1
        assert records[0].doctor_id == doctor_id

    def test_get_all_medical_records(self, db_session):
        record1 = MedicalRecordModel(doctor_id=uuid.uuid4(), patient_id=uuid.uuid4())
        record2 = MedicalRecordModel(doctor_id=uuid.uuid4(), patient_id=uuid.uuid4())
        db_session.add_all([record1, record2])
        db_session.commit()
        
        service = MedicalRecordService(db_session)
        records = service.get_all_medical_records(skip=0, limit=1)
        
        assert len(records) == 1
