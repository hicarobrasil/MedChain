import pytest
from fastapi import status
from app.main import app
from app.auth.schemas import DoctorRegisterModel
from app.models.doctor import SpecialtyEnum

def test_register_doctor_duplicate_crm(client, db_session):
    # Setup: Criar médico existente com o CRM
    from app.models.user import UserModel, StatusEnum
    from app.models.doctor import DoctorModel
    
    user = UserModel(full_name="Doctor Existing", email="exist@test.com", password="hash", status=StatusEnum.ACTIVE)
    db_session.add(user)
    db_session.commit()
    doctor = DoctorModel(user_id=user.id, CRM="123456", specialty=SpecialtyEnum.GENERAL)
    db_session.add(doctor)
    db_session.commit()
    
    # Tentar registrar novo médico com mesmo CRM
    payload = {
        "email": "new@test.com",
        "password": "password123",
        "CRM": "123456",
        "specialty": SpecialtyEnum.GENERAL.value,
        "full_name": "Doctor New"
    }
    
    response = client.post("/api/v1/auth/register-doctor", json=payload)
    
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Este CRM já está cadastrado para outro médico."
