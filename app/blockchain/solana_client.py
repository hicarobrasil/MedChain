from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solana.rpc.api import Client
import base58
import hashlib
import json
import os
from typing import Dict, Any

class SolanaHashStorage:
    """Classe para armazenar hashes na blockchain da Solana, sem custo para o usuário."""

    def __init__(self, rpc_url="http://solana:8899"):
        """Inicializa o cliente Solana e carrega a chave mestre do sistema."""
        self.client = Client(rpc_url)
        self.system_keypair = self._load_system_keypair()

    def _load_system_keypair(self) -> Keypair:
        """Carrega ou cria uma chave mestre para pagar as transações."""
        keypair_path = os.path.expanduser("~/.config/solana/system_key.json")
        os.makedirs(os.path.dirname(keypair_path), exist_ok=True)

        if os.path.exists(keypair_path):
            with open(keypair_path, 'r') as f:
                keypair_data = json.load(f)
            return Keypair.from_secret_key(bytes(keypair_data))
        else:
            keypair = Keypair()
            with open(keypair_path, 'w') as f:
                json.dump(list(keypair.secret_key), f)
            print(f"Nova chave mestre criada: {keypair.public_key}")
            return keypair

    def check_balance(self) -> int:
        """Verifica o saldo da chave mestre."""
        return self.client.get_balance(self.system_keypair.public_key)["result"]["value"]

    def airdrop_sol(self, amount=1):
        """Solicita SOL grátis (apenas em ambiente de testes)."""
        return self.client.request_airdrop(self.system_keypair.public_key, amount * 10**9)

    def hash_file(self, file_data: bytes) -> str:
        """Cria um hash SHA-256 dos dados do arquivo."""
        return hashlib.sha256(file_data).hexdigest()

    def store_file_hash(self, file_id: str, file_hash: str) -> str:
        """
        Armazena um hash na blockchain da Solana.

        Args:
            file_id: ID do arquivo.
            file_hash: Hash SHA-256 do arquivo.

        Returns:
            ID da transação.
        """
        memo_program_id = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
        memo_data = f"MEDIVAULT:FILE:{file_id}:{file_hash}".encode()

        memo_instruction = {
            'keys': [{'pubkey': self.system_keypair.public_key, 'isSigner': True, 'isWritable': True}],
            'programId': memo_program_id,
            'data': base58.b58encode(memo_data)
        }

        transaction = Transaction().add(memo_instruction)
        result = self.client.send_transaction(transaction, self.system_keypair)

        return result['result']

    def verify_file(self, file_id: str, file_data: bytes, transaction_id: str) -> bool:
        """
        Verifica se um arquivo corresponde ao hash armazenado na blockchain.

        Args:
            file_id: ID do arquivo.
            file_data: Dados do arquivo.
            transaction_id: ID da transação Solana.

        Returns:
            True se o hash estiver correto, False caso contrário.
        """
        file_hash = self.hash_file(file_data)
        tx_data = self.client.get_transaction(transaction_id)

        if not tx_data['result']:
            return False

        tx_message = tx_data['result']['transaction']['message']
        return f"MEDIVAULT:FILE:{file_id}:{file_hash}" in str(tx_message)
