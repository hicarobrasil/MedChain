import os
import json
import uuid
import hashlib
from base64 import b64decode
import requests
import json

from solathon import Client, Keypair, PublicKey, Transaction
from solathon.core.instructions import Instruction, AccountMeta, transfer
from solathon.utils import sol_to_lamport

class SolanaHashStorage:
    
    def __init__(self,wallet_file="solana_wallet.json", local=False):
        
        if local:
            self.client = Client("http://localhost:8899", local=True)
        else:
            self.client = Client("https://api.devnet.solana.com")

        self.wallet_file = wallet_file
        self.keypair = self._load_or_create_keypair()
        print(f"Chave pública: {str(self.keypair.public_key)}")

    def _load_or_create_keypair(self) -> Keypair:
        """
        Carrega um keypair existente do arquivo JSON ou cria um novo se não existir.
        """
        if os.path.exists(self.wallet_file):
            try:
                # Usar o método nativo from_file da classe Keypair
                keypair = Keypair.from_file(self.wallet_file)
                print(f"Carregando wallet existente: {str(keypair.public_key)}")
                return keypair
            except Exception as e:
                print(f"Erro ao carregar wallet: {e}")
                print("Criando nova wallet...")
        
        # Criar nova keypair se não existe ou houve erro
        keypair = Keypair()
        
        # Converter a chave privada para uma lista de inteiros para salvar no arquivo
        private_key_bytes = keypair.key_pair.encode()
        private_key_list = [b for b in private_key_bytes]
        
        # Salvar no formato esperado pelo método from_file
        with open(self.wallet_file, 'w') as f:
            json.dump(private_key_list, f)
        
        print(f"Nova wallet criada e salva em {self.wallet_file}")
        
        return keypair

    def get_balance(self) -> float:
        """
        Obtém o saldo atual da wallet em SOL.
        
        Returns:
            float: Saldo em SOL
        """
        try:
            balance_lamports = self.client.get_balance(self.keypair.public_key)
            return balance_lamports / 1e9
        except Exception as e:
            print(f"Erro ao verificar saldo: {e}")
            return 0.0

    def airdrop(self, amount: float = 1.0):
        """
        Solicita um airdrop para a conta do par de chaves na devnet.
        
        Args:
            amount: Quantidade de SOL a receber (padrão: 1.0)
            
        Returns:
            Resposta do airdrop
        """
        lamports = sol_to_lamport(amount)
        return self.client.request_airdrop(self.keypair.public_key, lamports)

    def generate_file_id(self) -> str:
        """
        Gera um ID único para um arquivo.
        
        Returns:
            str: UUID como string
        """
        return str(uuid.uuid4())

    def hash_file(self, data: bytes) -> str:
        """
        Gera um hash SHA-256 a partir do conteúdo do arquivo.
        
        Args:
            data: Conteúdo do arquivo em bytes
            
        Returns:
            str: Hash SHA-256 em formato hexadecimal
        """
        return hashlib.sha256(data).hexdigest()

    def extract_blockhash(self, response):
        """
        Extrai o blockhash da resposta do nó Solana.
        
        Args:
            response: Resposta do método get_latest_blockhash
            
        Returns:
            str: Blockhash
        """
        if isinstance(response, dict) and 'result' in response:
            if 'value' in response['result']:
                return response['result']['value']['blockhash']
            else:
                return response['result']['blockhash']
        elif hasattr(response, 'blockhash'):
            return response.blockhash
        elif hasattr(response, 'to_string'):
            return response.to_string()
        else:
            print(f"Formato do blockhash recebido: {type(response)}")
            print(f"Conteúdo: {response}")
            raise Exception("Não foi possível extrair o blockhash da resposta")

    def store_file_hash(
        self,
        file_id: str,
        file_hash: str,
        recipient: str = None,
        amount_sol: float = 0.0
    ) -> str:
        """
        Armazena o hash do arquivo na blockchain Solana.
        
        Args:
            file_id: ID único do arquivo
            file_hash: Hash SHA-256 do arquivo
            recipient: Endereço do destinatário (opcional)
            amount_sol: Quantidade de SOL a transferir (padrão: 0.0)
            
        Returns:
            str: ID da transação
        """
        try:
            to_pubkey = PublicKey(recipient) if recipient else self.keypair.public_key
            instructions = []

            if amount_sol > 0:
                # Se houver um valor em SOL, cria uma instrução de transferência
                lamports = sol_to_lamport(amount_sol)
                transfer_ix = transfer(
                    from_public_key=self.keypair.public_key,
                    to_public_key=to_pubkey,
                    lamports=lamports
                )
                instructions.append(transfer_ix)

            # Instrução de memo para armazenar o hash do arquivo
            memo_program_id = PublicKey("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
            memo_text = f"MEDIVAULT:FILE:{file_id}:{file_hash}"

            memo_instruction = Instruction(
                program_id=memo_program_id,
                keys=[AccountMeta(public_key=self.keypair.public_key, is_signer=True, is_writable=False)],
                data=memo_text.encode()
            )
            instructions.append(memo_instruction)

            # Criar e assinar transação
            transaction = Transaction(instructions=instructions, signers=[self.keypair])

            recent_blockhash_response = self.client.get_latest_blockhash()
            recent_blockhash = self.extract_blockhash(recent_blockhash_response)
            transaction.recent_blockhash = recent_blockhash
            print(f"Blockhash: {recent_blockhash}")

            print(f"Enviando transação com memo: {memo_text}")
            result = self.client.send_transaction(transaction)

            if isinstance(result, str) and len(result) > 40:
                return result
            elif isinstance(result, dict) and 'result' in result:
                return result['result']
            elif hasattr(result, 'tx_id'):
                return result.tx_id
            else:
                print(f"Erro na resposta da transação: {result}")
                return None

        except Exception as e:
            print(f"Erro ao enviar transação: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def verify_file(self, file_id: str, file_data: bytes, transaction_id: str) -> bool:
        """
        Verifica se o hash do arquivo corresponde ao registrado na blockchain.

        Args:   
            file_id: ID único do arquivo
            file_data: Conteúdo do arquivo em bytes
            transaction_id: ID da transação na blockchain

        returns:
            bool: True se o hash do arquivo corresponder ao registrado, False caso contrário
        """
        try:

            file_hash = self.hash_file(file_data)
            memo_text = f"MEDIVAULT:FILE:{file_id}:{file_hash}"
            
            # Chamada direta à API Solana
            response = requests.post(
                "https://api.devnet.solana.com",
                headers={"Content-Type": "application/json"},
                data=json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [transaction_id, {"encoding": "json", "maxSupportedTransactionVersion": 0}]
                })
            )
            
            # Verificar resultado
            data = response.json()
            if "result" not in data or not data["result"]:
                return False
                
            # Converter para string e verificar se contém o memo
            tx_json = json.dumps(data)
           
            if memo_text in tx_json:
                return True
                
            return False
            
        except Exception:
            return False