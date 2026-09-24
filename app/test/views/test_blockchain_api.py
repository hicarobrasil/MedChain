import pytest
from unittest.mock import patch

class TestBlockchainAPI:

    @patch("app.blockchain.routes.BlockchainService")
    def test_store_hash_success(self, mock_service_class, client):
        """
        Test Case 1 (Payload Válido): Envie um hash válido via POST. 
        Verifique o status code 201 e a estrutura do JSON de retorno.
        """
        # Setup mock
        mock_service = mock_service_class.return_value
        mock_service.store_file_hash.return_value = "fake_tx_id_view_123"
        
        payload = {
            "file_hash": "valid_sha256_hash_here",
            "file_id": "test_file_001"
        }
        
        response = client.post("/api/v1/blockchain/store-hash", json=payload)
        
        # Verificações
        assert response.status_code == 201
        data = response.json()
        assert data["blockchain_tx_id"] == "fake_tx_id_view_123"
        assert "success" in data["message"].lower()

    def test_store_hash_invalid_payload(self, client):
        """
        Test Case 2 (Payload Inválido/Missing): Envie requisições sem o parâmetro do hash. 
        Garanta o retorno de erro 422 (Unprocessable Entity - padrão FastAPI para validação).
        """
        # Payload sem 'file_hash'
        payload = {
            "file_id": "test_file_001"
        }
        
        response = client.post("/api/v1/blockchain/store-hash", json=payload)
        
        # Verificações
        assert response.status_code == 422
        assert "detail" in response.json()

    @patch("app.blockchain.routes.BlockchainService")
    def test_store_hash_service_error(self, mock_service_class, client):
        """
        Testa o tratamento de erro quando o serviço falha.
        """
        # Setup mock
        mock_service = mock_service_class.return_value
        mock_service.store_file_hash.side_effect = Exception("Solana transaction failed")
        
        payload = {
            "file_hash": "valid_hash",
        }
        
        response = client.post("/api/v1/blockchain/store-hash", json=payload)
        
        # Verificações
        assert response.status_code == 500
        assert "Error storing hash" in response.json()["detail"]
