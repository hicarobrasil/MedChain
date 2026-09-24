import base64
import os
from datetime import date, datetime, timezone

from cryptography.fernet import Fernet
from fastapi import status

from app.models.doctor import DoctorModel, SpecialtyEnum
from app.models.file import FileModel
from app.models.patient import GenderEnum, PatientModel
from app.models.user import StatusEnum, UserModel

CONTEUDO = b"conteudo-do-exame"


def _criar_arquivo(db_session, tmp_path):
    doctor_user = UserModel(
        full_name="Doctor", email="doc.file@test.com", password="hash", status=StatusEnum.ACTIVE
    )
    patient_user = UserModel(
        full_name="Patient", email="pat.file@test.com", password="hash", status=StatusEnum.ACTIVE
    )
    db_session.add_all([doctor_user, patient_user])
    db_session.commit()

    doctor = DoctorModel(user_id=doctor_user.id, CRM="999", specialty=SpecialtyEnum.GENERAL)
    patient = PatientModel(
        cellphone="123",
        birth_date=date(1990, 1, 1),
        gender=GenderEnum.MALE,
        user_id=patient_user.id,
    )
    db_session.add_all([doctor, patient])
    db_session.commit()

    caminho = tmp_path / "exame.bin"
    chave = os.environ["MEDICAL_RECORDS_API_CRYPTO_KEY"]
    caminho.write_bytes(Fernet(chave.encode()).encrypt(CONTEUDO))

    arquivo = FileModel(
        url=str(caminho),
        format="application/pdf",
        description="Exame",
        hash="hash-do-exame",
        created_date=datetime.now(timezone.utc),
        patient_uid=patient.public_id,
        doctor_uid=doctor.public_id,
    )
    db_session.add(arquivo)
    db_session.commit()
    db_session.refresh(arquivo)
    return arquivo, patient


def test_list_by_patient(authenticated_client, db_session, tmp_path):
    arquivo, patient = _criar_arquivo(db_session, tmp_path)

    response = authenticated_client.get(f"/api/v1/files/by-patient/{patient.public_id}/")

    assert response.status_code == status.HTTP_200_OK
    corpo = response.json()
    assert len(corpo) == 1
    assert corpo[0]["id"] == arquivo.id
    assert corpo[0]["description"] == "Exame"


def test_get_all_files_by_patient_traz_conteudo_decriptado(
    authenticated_client, db_session, tmp_path
):
    arquivo, patient = _criar_arquivo(db_session, tmp_path)

    response = authenticated_client.get(f"/api/v1/files/patient/{patient.public_id}/")

    assert response.status_code == status.HTTP_200_OK
    corpo = response.json()
    assert len(corpo) == 1
    assert corpo[0]["id"] == arquivo.id
    assert base64.b64decode(corpo[0]["content"]) == CONTEUDO


def test_download_file_retorna_conteudo_decriptado(authenticated_client, db_session, tmp_path):
    arquivo, _ = _criar_arquivo(db_session, tmp_path)

    response = authenticated_client.get(f"/api/v1/files/{arquivo.id}/content/")

    assert response.status_code == status.HTTP_200_OK
    assert response.content == CONTEUDO
