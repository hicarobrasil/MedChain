#!/usr/bin/env python3
"""
Script para testar a autenticacao JWT apos as correcoes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth.utils import create_access_token, decode_token
from app.settings import get_settings

def test_jwt_functions():
    """Testa as funcoes de criacao e decodificacao de JWT"""
    settings = get_settings()
    
    print("🔧 Testando funcoes JWT...")
    print(f"JWT_SECRET configurado: {'Sim' if settings.JWT_SECRET else 'Nao'}")
    print(f"JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
    
    test_user_data = {
        "email": "test@example.com",
        "user_uid": "123456789",
        "role": "user"
    }
    
    try:
        print("\n✅ Teste 1: Criando token...")
        token = create_access_token(test_user_data)
        print(f"Token criado: {token[:50]}...")
   
        print("\n✅ Teste 2: Decodificando token...")
        decoded_data = decode_token(token)
        
        if decoded_data:
            print("Token decodificado com sucesso!")
            print(f"Usuario: {decoded_data['user']['email']}")
            print(f"Role: {decoded_data['user']['role']}")
            print(f"Expira em: {decoded_data['exp']}")
        else:
            print("❌ Erro ao decodificar token")
            return False
            
        print("\n✅ Teste 3: Criando refresh token...")
        refresh_token = create_access_token(test_user_data, refresh=True, expiry_seconds=7*24*60*60)
        print(f"Refresh token criado: {refresh_token[:50]}...")
        
        decoded_refresh = decode_token(refresh_token)
        if decoded_refresh and decoded_refresh.get('refresh'):
            print("Refresh token criado e decodificado com sucesso!")
        else:
            print("❌ Erro ao criar/decodificar refresh token")
            return False
            
        print("\n🎉 Todos os testes passaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_jwt_functions()
    sys.exit(0 if success else 1)
