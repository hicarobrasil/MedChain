import pytest
from fastapi import status
from app.models.user import UserModel, StatusEnum
from app.models.doctor import DoctorModel, SpecialtyEnum

class TestDoctorAPI:

    def test_list_doctors_success(self, authenticated_client, db_session):
        # Setup: Criar um doctor para listar
        user = UserModel(full_name="Doctor List", email="doc_list@test.com", password="hash", status=StatusEnum.ACTIVE)
        db_session.add(user)
        db_session.commit()
        doctor = DoctorModel(user_id=user.id, CRM="123", specialty=SpecialtyEnum.GENERAL)
        db_session.add(doctor)
        db_session.commit()
        
        response = authenticated_client.get("/api/v1/doctors/")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1

    def test_get_doctor_success(self, authenticated_client, db_session):
        # Setup: Criar um doctor para buscar
        user = UserModel(full_name="Doctor Get", email="doc_get@test.com", password="hash", status=StatusEnum.ACTIVE)
        db_session.add(user)
        db_session.commit()
        doctor = DoctorModel(user_id=user.id, CRM="456", specialty=SpecialtyEnum.CARDIOLOGY)
        db_session.add(doctor)
        db_session.commit()
        
        response = authenticated_client.get(f"/api/v1/doctors/{doctor.public_id}/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["crm"] == "456"
        assert data["specialty"] == "CARDIOLOGY"

