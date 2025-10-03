#!/usr/bin/env python3
"""
Script para testar as funções de hash de senha
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth.utils import generate_passwd_hash, verify_password


def test_password_functions():
    """Testa as funções de hash e verificação de senha"""

    print("🔧 Testando funções de senha...")

    test_password = "minha_senha_secreta_123"

    try:
        print("\n✅ Teste 1: Gerando hash da senha...")
        password_hash = generate_passwd_hash(test_password)
        print(f"Hash gerado: {password_hash[:50]}...")

        print("\n✅ Teste 2: Verificando senha correta...")
        is_valid = verify_password(test_password, password_hash)
        if is_valid:
            print("Senha verificada com sucesso!")
        else:
            print("❌ Erro ao verificar senha correta")
            return False

        print("\n✅ Teste 3: Verificando senha incorreta...")
        is_invalid = verify_password("senha_errada", password_hash)
        if not is_invalid:
            print("Senha incorreta rejeitada corretamente!")
        else:
            print("❌ Erro: senha incorreta foi aceita")
            return False

        print("\n🎉 Todos os testes de senha passaram!")
        return True

    except Exception as e:
        print(f"❌ Erro durante os testes de senha: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_password_functions()
    sys.exit(0 if success else 1)
