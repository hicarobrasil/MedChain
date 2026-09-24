from fastapi import APIRouter
from app.doctor.views import DoctorView
from app.doctor.schemas import DoctorOut

router = APIRouter(tags=["Medico"])

router.get(
    "/{doctor_id}/dashboard-stats",
    name="get_doctor_dashboard_stats",
    status_code=200,
)(DoctorView.get_dashboard_stats)

router.get(
    "/{doctor_id}/patients",
    name="get_doctor_patients",
    status_code=200,
)(DoctorView.get_doctor_patients)

router.get(
    "/{doctor_id}/", name="get_doctor", response_model=DoctorOut, status_code=200
)(DoctorView.get_doctor)

router.post(
    "/",
    name="create_doctor",
    response_model=DoctorOut,
    status_code=201,
    responses={
        201: {"description": "Medico criado com sucesso"},
        400: {"description": "Dados invalidos"},
        500: {"description": "Erro interno do servidor"},
    },
)(DoctorView.create_doctor)

router.get(
    "/",
    name="list_doctors",
    status_code=200,
)(DoctorView.list_doctors)

router.put(
    "/{doctor_id}/",
    name="update_doctor",
    response_model=DoctorOut,
    status_code=200,
    responses={
        200: {"description": "Medico atualizado com sucesso"},
        404: {"description": "Medico nao encontrado"},
        401: {"description": "Dados invalidos"},
        403: {"description": "Acesso negado"},
        500: {"description": "Erro interno do servidor"},
    },
)(DoctorView.update_doctor)
