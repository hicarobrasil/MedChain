import pytest
from datetime import date
from uuid import uuid4
from fastapi import status
from app.main import app
from app.models.user import UserModel, StatusEnum
from app.models.doctor import DoctorModel, SpecialtyEnum
from app.models.patient import PatientModel, GenderEnum
from app.medical_record.enums import MedicalRecordTypes

class TestMedicalRecordAPI:

    def test_create_medical_record_success(self, authenticated_client, db_session):
        # Setup: Criar Doctor e Patient no banco de dados para evitar IntegrityError
        # Criar Usuario Doctor
        doctor_user = UserModel(full_name="Doctor Test", email="doctor@test.com", password="hash", status=StatusEnum.ACTIVE)
        db_session.add(doctor_user)
        db_session.commit()
        doctor = DoctorModel(user_id=doctor_user.id, CRM="123456", specialty=SpecialtyEnum.GENERAL)
        db_session.add(doctor)
        db_session.commit()

        # Criar Usuario Patient
        patient_user = UserModel(full_name="Patient Test", email="patient@test.com", password="hash", status=StatusEnum.ACTIVE)
        db_session.add(patient_user)
        db_session.commit()
        patient = PatientModel(cellphone="123456", birth_date=date(1990, 1, 1), gender=GenderEnum.MALE, user_id=patient_user.id)
        db_session.add(patient)
        db_session.commit()

        # Payload esperado pela view
        payload = {
            "type": MedicalRecordTypes.CONSULTATION.value,
            "data": {
                "doctor_id": str(doctor.public_id),
                "patient_id": str(patient.public_id),
                "chief_complaint": "Dor de cabeça",
                "history_of_present_illness": "Começou ontem",
                "diagnosis": "Enxaqueca",
                "treatment_plan": "Descanso e medicação"
            }
        }

        # A rota POST /api/v1/medical-records/ é chamada
        response = authenticated_client.post("/api/v1/medical-records/", json=payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert "medical_record_public_id" in response.json()

    def test_list_all_medical_records_success(self, authenticated_client):
        # Lista tudo
        response = authenticated_client.get("/api/v1/medical-records/")
        
        assert response.status_code == status.HTTP_200_OK
        assert "consultations" in response.json()
        assert "diagnostics" in response.json()
        assert "medical_certificates" in response.json()

    def test_list_medical_records_by_type_success(self, authenticated_client):
        # Filtra por tipo
        response = authenticated_client.get(f"/api/v1/medical-records/?type={MedicalRecordTypes.CONSULTATION.value}")
        
        assert response.status_code == status.HTTP_200_OK
        # Espera uma lista diretamente
        assert isinstance(response.json(), list)
