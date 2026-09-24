import pytest
import uuid
from unittest.mock import MagicMock, patch
from app.cron.sync_blockchain import sync_medical_records_to_blockchain
from app.models.medical_record import MedicalRecordModel

class TestBlockchainSyncJob:

    @patch("app.cron.sync_blockchain.BlockchainService")
    def test_sync_success(self, mock_blockchain_service_class, db_session):
        """
        Test Case 1 (Sucesso): Mocke a resposta da blockchain. Insira no banco MedicalRecordModel 
        com blockchain_tx_id vazio. Execute o cron. Valide se a função store_file_hash foi chamada 
        com o hash correto e se o banco foi atualizado.
        """
        # Setup mocks
        mock_blockchain_service = mock_blockchain_service_class.return_value
        mock_blockchain_service.store_file_hash.return_value = "tx_id_success_123"
        
        # Inserir registro no banco de teste
        record = MedicalRecordModel(
            public_id=uuid.uuid4(),
            hash="hash_para_sincronizar_123",
            blockchain_tx_id=None,
            doctor_id=uuid.uuid4(),
            patient_id=uuid.uuid4()
        )
        db_session.add(record)
        db_session.commit()
        
        # Executar o job passando a sessão de teste
        sync_medical_records_to_blockchain(db=db_session)
        
        # Verificações
        db_session.refresh(record)
        assert record.blockchain_tx_id == "tx_id_success_123"
        mock_blockchain_service.store_file_hash.assert_called_once_with(
            file_hash="hash_para_sincronizar_123",
            file_id=str(record.public_id)
        )

    @patch("app.cron.sync_blockchain.BlockchainService")
    def test_sync_no_pending_records(self, mock_blockchain_service_class, db_session):
        """
        Test Case 2 (Nenhum registro): Garanta que, se todos os registros já possuírem um 
        blockchain_tx_id, o cron finalize sem disparar chamadas para a Solana.
        """
        # Setup mocks
        mock_blockchain_service = mock_blockchain_service_class.return_value
        
        # Inserir registro já sincronizado
        record = MedicalRecordModel(
            public_id=uuid.uuid4(),
            hash="hash_ja_sincronizado",
            blockchain_tx_id="ja_tenho_id_456",
            doctor_id=uuid.uuid4(),
            patient_id=uuid.uuid4()
        )
        db_session.add(record)
        db_session.commit()
        
        # Executar o job
        sync_medical_records_to_blockchain(db=db_session)
        
        # Verificações
        mock_blockchain_service.store_file_hash.assert_not_called()

    @patch("app.cron.sync_blockchain.BlockchainService")
    def test_sync_blockchain_resilience(self, mock_blockchain_service_class, db_session):
        """
        Test Case 3 (Resiliência/Falha na Blockchain): Simule uma falha na chamada de store_file_hash. 
        Garanta que o erro seja tratado e que nenhum registro tenha o banco alterado indevidamente.
        """
        # Setup mocks
        mock_blockchain_service = mock_blockchain_service_class.return_value
        mock_blockchain_service.store_file_hash.side_effect = Exception("Solana Node Timeout")
        
        # Inserir registro pendente
        public_id = uuid.uuid4()
        record = MedicalRecordModel(
            public_id=public_id,
            hash="hash_falha_teste",
            blockchain_tx_id=None,
            doctor_id=uuid.uuid4(),
            patient_id=uuid.uuid4()
        )
        db_session.add(record)
        db_session.commit()
        
        # Executar o job
        sync_medical_records_to_blockchain(db=db_session)
        
        # Verificações - Re-fetch para evitar problemas de sessão expirada após rollback
        updated_record = db_session.query(MedicalRecordModel).filter_by(public_id=public_id).first()
        assert updated_record.blockchain_tx_id is None # Deve continuar nulo após a falha
