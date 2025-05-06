from app.blockchain.solana_client import SolanaHashStorage

# def main():
#     try:
#         # Inicializa usando o nó local configurado em http://localhost:8899
#         storage = SolanaHashStorage()

#         # Mostra o saldo atual
#         balance = storage.get_balance()
#         print("Saldo:", balance, "SOL")

#         # Faz um airdrop de 2 SOLs (somente funciona em testnet/devnet ou nó local habilitado)
#         print("Solicitando airdrop de 2 SOLs...")
#         storage.airdrop(2.0)

#         # Gera um ID e hash simulado para um arquivo
#         file_id = storage.generate_file_id()
#         file_data = "Conteúdo de teste do arquivo - versão simples".encode("utf-8")
#         file_hash = storage.hash_file(file_data)

#         # Envia o hash para a blockchain
#         print("Armazenando hash na blockchain...")
#         tx_id = storage.store_file_hash(file_id, file_hash)
#         print("ID da transação:", tx_id)

#         # Verifica a integridade do arquivo
#         if tx_id:
#             is_valid = storage.verify_file(file_id, file_data, tx_id)
#             print("Verificação:", "OK ✅" if is_valid else "Falhou ❌")
#         else:
#             print("Erro: não foi possível obter ID da transação.")

#     except Exception as e:
#         print("Erro durante o teste:", e)

# if __name__ == "__main__":
#     main()

def main():
    print("== Iniciando teste de verificação com debugging ==")
    
    storage = SolanaHashStorage()
    print(f"Inicializado cliente Solana para {storage.client.endpoint}")
    
    # Dados de teste do seu exemplo original
    file_id = "4fee71eb-847f-4dd4-b7e0-db367ed4ba0f"
    file_data = "Conteúdo de teste do arquivo - versão simples".encode("utf-8")
    tx_id = "EEP3KvR3XHECtdn7UYUgLv2bV6i6Fo694cUUpX5SzKPCbkMUtZeQphWxsFSt35hbac2mb5NYXzc3sZTvmEG9YJ4"
    
    print("\n=== Teste de recálculo do hash ===")
    recalculated_hash = storage.hash_file(file_data)
    print(f"Hash recalculado: {recalculated_hash}")
    
    print("\n=== Verificando a transação ===")
    is_valid = storage.verify_file(file_id, file_data, tx_id)

    print("\n=== Resultado ===")
    if is_valid:
        print("Verificação: OK ✅")
    else:
        print("Verificação: Falhou ❌")
        print("Isso pode acontecer devido a:")
        print("1. O hash recalculado não corresponde ao registrado")
        print("2. O formato da resposta da API Solana mudou")
        print("3. A transação não contém o memo esperado")
        print("4. O conteúdo do arquivo mudou desde o registro")

if __name__ == "__main__":
    main()