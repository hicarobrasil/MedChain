from fastapi import APIRouter

from app.file.views import FileView

router = APIRouter(tags=["Arquivo"])

router.post(
    "/upload/",
    name="upload_file",
    status_code=201,
)(FileView.upload_file)

router.get(
    "/by-patient/{patient_uid}/",
    name="list_files_by_patient",
    status_code=200,
)(FileView.list_by_patient)

router.get(
    "/{file_id}/content/",
    name="download_file_content",
    status_code=200,
)(FileView.download_file)

router.get(
    "/{file_id}/",
    name="get_file_by_id",
    status_code=200,
)(FileView.get_file)

router.get(
    "/patient/{patient_uid}/",
    name="get_files_by_patient",
    status_code=200,
)(FileView.get_all_files_by_patient)
