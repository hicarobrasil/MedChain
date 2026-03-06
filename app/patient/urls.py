from fastapi import APIRouter

from app.patient.views import PatientView

router = APIRouter(tags=["Prontuario"])

router.get(
    "/",
    name="list_all_patients",
    responses={
        200: {"description": "Pacientes encontrados com sucesso"},
        401: {"description": "Usuario nao autenticado"},
        403: {"description": "Acesso negado"},
        500: {"description": "Erro interno do servidor"},
    },
)(PatientView.get_all)

router.post(
    "/",
    name="create_patient",
    responses={
        200: {"description": "Paciente criado com sucesso"},
        401: {"description": "Usuario nao autenticado"},
        403: {"description": "Acesso negado"},
        500: {"description": "Erro interno do servidor"},
    },
)(PatientView.post)

router.get(
    "/{patient_uid}/",
    name="get_patient_by_uid",
    responses={
        200: {"description": "Paciente encontrado com sucesso"},
        401: {"description": "Usuario nao autenticado"},
        403: {"description": "Acesso negado"},
        404: {"description": "Paciente nao encontrado"},
        500: {"description": "Erro interno do servidor"},
    },
)(PatientView.get)

router.put(
    "/{patient_uid}/",
    name="update_patient_by_uid",
    responses={
        200: {"description": "Paciente atualizado com sucesso"},
        401: {"description": "Usuario nao autenticado"},
        403: {"description": "Acesso negado"},
        404: {"description": "Paciente nao encontrado"},
        500: {"description": "Erro interno do servidor"},
    },
)(PatientView.put)
