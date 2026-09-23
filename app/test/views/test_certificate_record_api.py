import pytest
from fastapi import status
from app.medical_record.enums import MedicalRecordTypes
from app.models.user import UserModel, StatusEnum
from app.models.doctor import DoctorModel, SpecialtyEnum
from app.models.patient import PatientModel, GenderEnum
from datetime import date

def test_create_medical_certificate_success(authenticated_client, db_session):
    # Setup
    doctor_user = UserModel(full_name="Doctor", email="doc_cert@test.com", password="hash", status=StatusEnum.ACTIVE)
    db_session.add(doctor_user)
    db_session.commit()
    doctor = DoctorModel(user_id=doctor_user.id, CRM="123", specialty=SpecialtyEnum.GENERAL)
    db_session.add(doctor)
    db_session.commit()

    patient_user = UserModel(full_name="Patient", email="pat_cert@test.com", password="hash", status=StatusEnum.ACTIVE)
    db_session.add(patient_user)
    db_session.commit()
    patient = PatientModel(cellphone="123", birth_date=date(1990, 1, 1), gender=GenderEnum.MALE, user_id=patient_user.id)
    db_session.add(patient)
    db_session.commit()

    # Payload Medical Certificate
    payload = {
        "type": MedicalRecordTypes.MEDICAL_CERTIFICATE.value,
        "data": {
            "doctor_id": str(doctor.public_id),
            "patient_id": str(patient.public_id),
            "purpose": "Atestado médico de repouso",
            "period_of_leave": "3 dias"
        }
    }

    response = authenticated_client.post("/api/v1/medical-records/", json=payload)
    
    assert response.status_code == status.HTTP_201_CREATED
    assert "medical_record_public_id" in response.json()
    assert "medical_certificate" in response.json()
