import pytest
import uuid
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.service.doctor_record_service import DoctorService
from app.models.doctor import DoctorModel, SpecialtyEnum
from app.models.user import StatusEnum

@pytest.fixture
def db_session():
    return MagicMock()

@pytest.fixture
def doctor_service(db_session):
    return DoctorService(db_session)

def test_create_doctor_success(doctor_service, db_session):
    data = {
        "crm": "12345",
        "specialty": SpecialtyEnum.CARDIOLOGY.value,
        "status": StatusEnum.ACTIVE.value,
        "user_id": 1
    }
    
    doctor = doctor_service.create_doctor(data)
    
    assert doctor.CRM == "12345"
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()

def test_create_doctor_invalid_specialty(doctor_service):
    data = {
        "crm": "12345",
        "specialty": 999, # Invalida
        "user_id": 1
    }
    
    with pytest.raises(HTTPException) as excinfo:
        doctor_service.create_doctor(data)
    assert excinfo.value.status_code == 400
