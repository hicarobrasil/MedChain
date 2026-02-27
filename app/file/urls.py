from fastapi import APIRouter

from app.file.views import FileView

router = APIRouter(tags=["Arquivo"])

router.post(
    "/upload/",
    name="upload_file",
    status_code=201,
)(FileView.upload_file)

router.get(
    "/{file_id}/",
    name="get_file_by_id",
    status_code=200,
)(FileView.get_file)
