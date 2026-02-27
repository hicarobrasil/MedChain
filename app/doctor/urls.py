from fastapi import APIRouter
from app.doctor.views import DoctorView
from app.doctor.schemas import DoctorOut

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
        400: {"description": "Dados inválidos"},
        500: {"description": "Erro interno do servidor"},
    },
)(DoctorView.create_doctor)

router.get(
    "/",
    name="get_doctor",
    response_model=DoctorOut,
    status_code=200,
    responses={
        200: {"description": "Médico encontrado com sucesso"},
        404: {"description": "Médico não encontrado"},
        401: {"description": "Dados inválidos"},
        403: {"description": "Acesso negado"},
        500: {"description": "Erro interno do servidor"},
    },
)(DoctorView.get_doctor)

router.put(
    "/{doctor_id}/",
    name="update_doctor",
    response_model=DoctorOut,
    status_code=200,
    responses={
        200: {"description": "Médico atualizado com sucesso"},
        404: {"description": "Médico não encontrado"},
        401: {"description": "Dados inválidos"},
        403: {"description": "Acesso negado"},
        500: {"description": "Erro interno do servidor"},
    },
)(DoctorView.update_doctor)
