from fastapi import APIRouter
from app.medical_record.views import MedicalRecordsView
from typing import Union, List, Dict

router = APIRouter(tags=["Prontuario Medico"])

router.get(
    "/",
    name="get_all_by_type_medical_records",
    response_model=Union[List, Dict],
    status_code=200,
)(MedicalRecordsView.get_all)

router.post(
    "/",
    name="create_medical_record",
    response_model=dict,
    status_code=201,
)(MedicalRecordsView.post)

router.get(
    "/{public_id}/",
    name="get_by_public_id",
    response_model=dict,
    status_code=200,
)(MedicalRecordsView.get_by_public_id)

router.get(
    "/{username}/",
    name="get_by_patient_username",
    response_model=list,
    status_code=200,
)(MedicalRecordsView.get_by_patient_username)
