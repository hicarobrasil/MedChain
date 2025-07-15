#!/usr/bin/env python3
"""
Teste simples do sistema
"""

import requests
import json

def test_simple():
    """Teste básico de endpoints"""
    
    BASE_URL = "http://127.0.0.1:8000/api/v1"
    
    # Teste de login
    login_data = {
        "email": "admin@medchain.com", 
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("✅ Login funcionando")
            
            # Teste simples de endpoint protegido
            headers = {"Authorization": f"Bearer {token}"}
            profile_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            print(f"Profile status: {profile_response.status_code}")
            
            if profile_response.status_code == 200:
                print("✅ Autenticação funcionando")
                return True
            
        print(f"❌ Erro: {response.text}")
        return False
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    test_simple()
