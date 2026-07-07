import pytest
from unittest.mock import MagicMock, patch
from app.service.blockchain_service import BlockchainService

class TestBlockchainService:

    @patch("app.service.blockchain_service.SolanaHashStorage")
    def test_store_file_hash_calls_client(self, mock_solana_storage_class):
        """
        Test Case 1 (Isolamento da API externa): Teste a função interna store_file_hash 
        mockando a biblioteca cliente da Solana.
        """
        # Setup mock
        mock_storage = mock_solana_storage_class.return_value
        mock_storage.store_file_hash.return_value = "tx_id_from_client_789"
        
        service = BlockchainService()
        file_hash = "abc_hash_123"
        file_id = "file_unique_id"
        
        # Execução
        tx_id = service.store_file_hash(file_hash, file_id)
        
        # Verificações
        assert tx_id == "tx_id_from_client_789"
        mock_storage.store_file_hash.assert_called_once_with(file_id, file_hash)

    @patch("app.service.blockchain_service.SolanaHashStorage")
    def test_store_file_hash_generates_uuid_if_missing(self, mock_solana_storage_class):
        """
        Verifica se um UUID é gerado se o file_id não for fornecido.
        """
        mock_storage = mock_solana_storage_class.return_value
        mock_storage.store_file_hash.return_value = "tx_id_123"
        
        service = BlockchainService()
        service.store_file_hash("some_hash")
        
        # Verifica se foi chamado com um file_id (gerado automaticamente)
        args, kwargs = mock_storage.store_file_hash.call_args
        assert len(args[0]) > 30 # Deve ser um UUID string
        assert args[1] == "some_hash"

    @patch("app.service.blockchain_service.SolanaHashStorage")
    def test_store_file_hash_failure(self, mock_solana_storage_class):
        """
        Verifica se a exceção é lançada quando o cliente Solana falha.
        """
        mock_storage = mock_solana_storage_class.return_value
        mock_storage.store_file_hash.return_value = None # Simula erro no cliente
        
        service = BlockchainService()
        
        with pytest.raises(Exception) as excinfo:
            service.store_file_hash("hash")
        
        assert "Failed to store hash" in str(excinfo.value)
