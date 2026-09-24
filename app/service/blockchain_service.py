from app.blockchain.solana_client import SolanaHashStorage
import uuid

class BlockchainService:
    def __init__(self):
        self.solana_client = SolanaHashStorage()

    def store_file_hash(self, file_hash: str, file_id: str = None) -> str:
        """
        Stores a file hash on the Solana blockchain using the Memo Program.
        
        Args:
            file_hash: The SHA-256 hash of the file.
            file_id: Optional unique identifier for the file. If not provided, a UUID will be generated.
            
        Returns:
            str: The blockchain transaction ID.
            
        Raises:
            Exception: If the transaction fails.
        """
        if not file_id:
            file_id = str(uuid.uuid4())
            
        tx_id = self.solana_client.store_file_hash(file_id, file_hash)
        
        if not tx_id:
            raise Exception("Failed to store hash on Solana blockchain")
            
        return tx_id
