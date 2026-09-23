import pytest
import uuid
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.models.doctor import DoctorModel, SpecialtyEnum
from app.models.user import StatusEnum
from app.service.doctor_record_service import DoctorService

class TestDoctorService:

    @pytest.fixture
    def doctor_service(self, db_session):
        return DoctorService(db_session)

    def test_create_doctor_success(self, doctor_service, db_session):
        data = {
            "crm": "12345",
            "specialty": "CARDIOLOGY",
            "status": "ACTIVE",
            "user_id": 1
        }
        
        doctor = doctor_service.create_doctor(data)
        
        assert doctor.CRM == "12345"
        assert doctor.specialty == SpecialtyEnum.CARDIOLOGY
        assert doctor.id is not None

    def test_create_doctor_invalid_specialty(self, doctor_service):
        data = {
            "crm": "12345",
            "specialty": "INVALID",
            "status": "ACTIVE",
            "user_id": 1
        }
        
        with pytest.raises(HTTPException) as excinfo:
            doctor_service.create_doctor(data)
        assert excinfo.value.status_code == 400

    def test_get_doctor_by_uid_success(self, doctor_service, db_session):
        doctor = DoctorModel(CRM="12345", specialty=SpecialtyEnum.CARDIOLOGY, user_id=1)
        db_session.add(doctor)
        db_session.commit()
        
        fetched_doctor = doctor_service.get_doctor_by_uid(doctor.public_id)
        assert fetched_doctor.CRM == "12345"

    def test_get_doctor_by_uid_not_found(self, doctor_service):
        with pytest.raises(HTTPException) as excinfo:
            doctor_service.get_doctor_by_uid(uuid.uuid4())
        assert excinfo.value.status_code == 404

    def test_get_doctor_by_crm_success(self, doctor_service, db_session):
        doctor = DoctorModel(CRM="12345", specialty=SpecialtyEnum.CARDIOLOGY, user_id=1)
        db_session.add(doctor)
        db_session.commit()
        
        fetched_doctor = doctor_service.get_doctor_by_crm("12345")
        assert fetched_doctor.CRM == "12345"

    def test_get_all_doctors(self, doctor_service, db_session):
        doctor1 = DoctorModel(CRM="1", specialty=SpecialtyEnum.CARDIOLOGY, user_id=1)
        doctor2 = DoctorModel(CRM="2", specialty=SpecialtyEnum.NEUROLOGY, user_id=2)
        db_session.add_all([doctor1, doctor2])
        db_session.commit()
        
        doctors = doctor_service.get_all_doctors()
        assert len(doctors) == 2

    def test_get_doctors_by_specialty(self, doctor_service, db_session):
        doctor1 = DoctorModel(CRM="1", specialty=SpecialtyEnum.CARDIOLOGY, user_id=1)
        doctor2 = DoctorModel(CRM="2", specialty=SpecialtyEnum.NEUROLOGY, user_id=2)
        db_session.add_all([doctor1, doctor2])
        db_session.commit()
        
        doctors = doctor_service.get_doctors_by_specialty(SpecialtyEnum.CARDIOLOGY)
        assert len(doctors) == 1
        assert doctors[0].CRM == "1"

    def test_update_doctor_success(self, doctor_service, db_session):
        doctor = DoctorModel(CRM="12345", specialty=SpecialtyEnum.CARDIOLOGY, user_id=1)
        db_session.add(doctor)
        db_session.commit()
        
        updated_doctor = doctor_service.update_doctor(doctor.public_id, {"CRM": "54321"})
        assert updated_doctor.CRM == "54321"

    def test_update_doctor_invalid_specialty(self, doctor_service, db_session):
        doctor = DoctorModel(CRM="12345", specialty=SpecialtyEnum.CARDIOLOGY, user_id=1)
        db_session.add(doctor)
        db_session.commit()
        
        with pytest.raises(HTTPException) as excinfo:
            doctor_service.update_doctor(doctor.public_id, {"specialty": 999})
        assert excinfo.value.status_code == 400

    def test_update_doctor_invalid_status(self, doctor_service, db_session):
        doctor = DoctorModel(CRM="12345", specialty=SpecialtyEnum.CARDIOLOGY, user_id=1)
        db_session.add(doctor)
        db_session.commit()
        
        with pytest.raises(HTTPException) as excinfo:
            doctor_service.update_doctor(doctor.public_id, {"status": 999})
        assert excinfo.value.status_code == 400

    def test_delete_doctor(self, doctor_service, db_session):
        doctor = DoctorModel(CRM="12345", specialty=SpecialtyEnum.CARDIOLOGY, user_id=1)
        db_session.add(doctor)
        db_session.commit()
        
        doctor_uid = doctor.public_id
        doctor_service.delete_doctor(doctor_uid)
        
        with pytest.raises(HTTPException):
            doctor_service.get_doctor_by_uid(doctor_uid)
