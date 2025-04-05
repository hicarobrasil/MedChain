from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.views.main import router as medical_records_router

def create_app():
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
    
    @app.get("/", tags=["Status"])
    async def root():
        return {"status": "online", "service": "MediVault API"}
    
    return app