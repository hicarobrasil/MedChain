#!/usr/bin/env python3
"""
Teste para verificar endpoint de medical records
"""

import requests
import json
from uuid import uuid4

def test_medical_record_endpoint():
    """Testa o endpoint de criação de medical record"""
    
    print("🏥 Testando endpoint de medical records...")
    
    BASE_URL = "http://127.0.0.1:8000/api/v1"
    
    # Primeiro, obter token de admin
    admin_login = {
        "email": "admin@medchain.com",
        "password": "admin123"
    }
    
    try:
        # Login
        login_response = requests.post(f"{BASE_URL}/auth/login", json=admin_login)
        if login_response.status_code != 200:
            print(f"❌ Erro no login: {login_response.text}")
            return False
            
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Criar médico para usar no teste
        doctor_data = {
            "name": "Dr. Teste Medical Record",
            "crm": f"CRM{int(uuid4().hex[:8], 16)}",
            "specialty": "GENERAL",
            "email": f"dr.teste{int(uuid4().hex[:8], 16)}@hospital.com",
            "phone": "+5511999999999",
            "status": "ACTIVE"
        }
        
        doctor_response = requests.post(f"{BASE_URL}/doctors/", json=doctor_data, headers=headers)
        if doctor_response.status_code != 201:
            print(f"❌ Erro ao criar médico: {doctor_response.text}")
            return False
            
        doctor_id = doctor_response.json()["uid"]
        print(f"✅ Médico criado: {doctor_id}")
        
        # Dados do medical record
        medical_record_data = {
            "patient_id": 1,  # Assumindo que existe um paciente com ID 1
            "doctor_id": doctor_id,
            "description": "Consulta de rotina - teste automatizado",
            "medications": '["Paracetamol", "Dipirona"]'
        }
        
        # Testar criação de medical record
        print("\n📝 Criando medical record...")
        record_response = requests.post(
            f"{BASE_URL}/medical-records/", 
            data=medical_record_data, 
            headers=headers
        )
        
        print(f"Status: {record_response.status_code}")
        
        if record_response.status_code == 201:
            record = record_response.json()
            print("✅ Medical record criado com sucesso!")
            print(f"ID: {record['id']}")
            print(f"Patient ID: {record['patient_id']}")
            print(f"Doctor ID: {record['doctor_id']}")
            print(f"Description: {record['description']}")
            return True
        else:
            print(f"❌ Erro ao criar medical record: {record_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    success = test_medical_record_endpoint()
    if success:
        print("\n🎉 Endpoint de medical records funcionando!")
    else:
        print("\n💥 Teste falhou.")
