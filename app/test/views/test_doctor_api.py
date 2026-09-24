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

    def test_create_doctor_success(self, authenticated_client):
        payload = {
            "CRM": "789",
            "specialty": "PEDIATRICS",
            "full_name": "Doctor Create",
            "email": "doc_create@test.com",
            "password": "senha123",
        }

        response = authenticated_client.post("/api/v1/doctors/", json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Doctor Create"
        assert data["crm"] == "789"
        assert data["specialty"] == "PEDIATRICS"

    def test_update_doctor_success(self, authenticated_client, db_session):
        user = UserModel(
            full_name="Doctor Update", email="doc_update@test.com", password="hash", status=StatusEnum.ACTIVE
        )
        db_session.add(user)
        db_session.commit()
        doctor = DoctorModel(user_id=user.id, CRM="321", specialty=SpecialtyEnum.GENERAL)
        db_session.add(doctor)
        db_session.commit()

        response = authenticated_client.put(
            f"/api/v1/doctors/{doctor.public_id}/",
            json={
                "CRM": "654",
                "specialty": "NEUROLOGY",
                "full_name": "Doctor Atualizado",
                "email": "doc_update@test.com",
                "password": "senha123",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["crm"] == "654"
        assert data["specialty"] == "NEUROLOGY"
        assert data["name"] == "Doctor Atualizado"

