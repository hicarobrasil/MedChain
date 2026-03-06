import os
import sys

# Forca UTF-8 no Windows ANTES de carregar o banco (evita UnicodeDecodeError no psycopg2)
if sys.platform == "win32":
    os.environ.setdefault("PGCLIENTENCODING", "UTF8")
    os.environ.setdefault("PYTHONUTF8", "1")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.doctor.urls import router as doctor_router
from app.medical_record.urls import router as medical_records_router
from app.patient.urls import router as pacient_records_router
from app.file.urls import router as file_router
from app.auth.routes import auth_router
from app.database import init_db
import logging

# Initialize the database (nao bloqueia a app se falhar)
try:
    init_db()
except Exception as e:
    logging.warning(f"init_db falhou (rotas ainda disponiveis): {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="MediVault API",
        description="API para gerenciamento de registros medicos com verificacao blockchain",
        version="1.0.0",
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em producao, especificar origens permitidas
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Registrar rotas
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(doctor_router, prefix="/api/v1/doctors")
    app.include_router(pacient_records_router, prefix="/api/v1/patients")
    app.include_router(medical_records_router, prefix="/api/v1/medical-records")
    app.include_router(file_router, prefix="/api/v1/files")

    return app


# Create application instance
app = create_app()
