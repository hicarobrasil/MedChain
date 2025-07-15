from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.views.medical_record_api import router as medical_records_router
from app.views.pacient_record_api import router as pacient_records_router
from app.auth.routes import auth_router
from app.doctor.routes import doctor_router
from app.database import init_db

# Initialize the database
init_db()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="MediVault API",
        description="API para gerenciamento de registros médicos com verificação blockchain",
        version="1.0.0"
    )
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção, especificar origens permitidas
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Registrar rotas
    app.include_router(medical_records_router, prefix="/api/v1")
    app.include_router(pacient_records_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(doctor_router, prefix="/api/v1")


    
    return app

# Create application instance
app = create_app()

