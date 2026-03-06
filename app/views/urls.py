
from fastapi import APIRouter
from typing import List
from app.views.medical_record_api import MedicalRecordsView, MedicalRecordsResponse


router = APIRouter(tags=["Prontuario"])

router.get(
    "/", name="list_all_medical_records", response_model=List[MedicalRecordsResponse]
)(MedicalRecordsView.get)