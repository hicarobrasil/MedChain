from fastapi import APIRouter
from typing import List
from app.doctor.views import DoctorView
from app.doctor.schemas import DoctorOut, DoctorIn

router = APIRouter(tags=["Médico"])

router.get(
    "/{doctor_id}/", name="get_doctor", response_model=DoctorOut, status_code=200
)(DoctorView.get_doctor)

router.post(
    "/",
    name="create_doctor",
    response_model=DoctorOut,
    status_code=201,
    responses={
        201: {"description": "Médico criado com sucesso"},
        401: {"description": "Usuário não autenticado"},
        403: {"description": "Acesso negado"},
    },
)(DoctorView.create_doctor)
