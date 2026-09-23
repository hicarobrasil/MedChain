import pytest
from faker import Faker
from datetime import datetime, timezone
import uuid

from app.models.address import AddressModel
from app.models.consultation import ConsultationModel
from app.models.diagnostic import DiagnosticModel
from app.models.doctor import DoctorModel
from app.models.file import FileModel
from app.models.login_record import User as LoginRecordModel
from app.models.medical_certificated import MedicalCertificatedModel
from app.models.medical_record import MedicalRecordModel
from app.models.patient import PatientModel
from app.models.prescription_item import PrescriptionItemModel
from app.models.prescription import PrescriptionModel
from app.models.user import UserModel, StatusEnum
from app.models.patient import GenderEnum

fake = Faker()

def test_user_model_creation():
    user = UserModel(
        full_name=fake.name(),
        email=fake.email(),
        password=fake.password(),
        status=StatusEnum.ACTIVE
    )
    assert user.full_name is not None
    assert user.email is not None

def test_address_model_creation():
    address = AddressModel(
        street=fake.street_name(),
        number=fake.building_number(),
        neighborhood=fake.secondary_address(),
        city=fake.city(),
        state=fake.state(),
        patient_id=1
    )
    assert address.street is not None
    assert address.patient_id == 1

def test_patient_model_creation():
    patient = PatientModel(
        cellphone=fake.phone_number()[:15],
        birth_date=fake.date_time_this_century(),
        gender=GenderEnum.MALE,
        user_id=1
    )
    assert patient.cellphone is not None
    assert patient.user_id == 1

def test_doctor_model_creation():
    doctor = DoctorModel(
        CRM=fake.bothify(text='CRM-######'),
        specialty='CARDIOLOGY',
        user_id=1
    )
    assert doctor.CRM is not None
    assert doctor.user_id == 1

def test_consultation_model_creation():
    consultation = ConsultationModel(
        chief_complaint=fake.text(),
        history_of_present_illness=fake.text(),
        diagnosis=fake.text(),
        treatment_plan=fake.text(),
        medical_record_id=1
    )
    assert consultation.chief_complaint is not None
    assert consultation.medical_record_id == 1

def test_diagnostic_model_creation():
    diagnostic = DiagnosticModel(
        description=fake.text(),
        issue_date=fake.date_time_this_year(),
        medical_record_id=1
    )
    assert diagnostic.description is not None
    assert diagnostic.medical_record_id == 1

def test_file_model_creation():
    # Corrected keyword arguments based on models/file.py
    # Patient model uses public_id as foreign key, not id.
    # For now, passing a dummy uuid to satisfy type checker
    file = FileModel(
        url=fake.url(),
        format=fake.file_extension(),
        hash=fake.sha256(),
        patient_uid=uuid.uuid4(),
        doctor_uid=uuid.uuid4()
    )
    assert file.url is not None

def test_login_record_model_creation():
    login_record = LoginRecordModel(
        username=fake.user_name(),
        email=fake.email(),
        password_hash=fake.password(),
        role="user"
    )
    assert login_record.username is not None

def test_medical_certificated_model_creation():
    # Corrected keyword arguments based on models/medical_certificated.py
    cert = MedicalCertificatedModel(
        purpose=fake.text(),
        period_of_leave=str(fake.random_int(min=1, max=30)),
        medical_record_id=1
    )
    assert cert.purpose is not None
    assert cert.medical_record_id == 1

def test_medical_record_model_creation():
    # Corrected keyword arguments based on models/medical_record.py
    record = MedicalRecordModel(
        doctor_id=uuid.uuid4(),
        patient_id=uuid.uuid4()
    )
    assert record.doctor_id is not None
    assert record.patient_id is not None

def test_prescription_item_model_creation():
    # Check model for correct field names
    item = PrescriptionItemModel(
        medication_name=fake.word(),
        dosage=fake.word(),
        prescription_id=1
    )
    assert item.medication_name is not None
    assert item.prescription_id == 1

def test_prescription_model_creation():
    # Corrected keyword arguments based on models/prescription.py
    prescription = PrescriptionModel(
        consultation_id=1
    )
    assert prescription.consultation_id == 1
