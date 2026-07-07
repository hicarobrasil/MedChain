import os
import sys
import asyncio
import logging
from contextlib import asynccontextmanager

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
from app.blockchain.routes import router as blockchain_router
from app.database import init_db
from app.cron.sync_blockchain import sync_medical_records_to_blockchain

# Initialize the database (nao bloqueia a app se falhar)
try:
    init_db()
except Exception as e:
    logging.warning(f"init_db falhou (rotas ainda disponiveis): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação, iniciando tarefas em segundo plano.
    """
    # Background task para sincronização blockchain
    async def blockchain_sync_worker():
        logging.info("Iniciando worker de sincronização blockchain...")
        while True:
            try:
                # Executa o job de sincronização em uma thread separada para não bloquear o loop de eventos
                await asyncio.to_thread(sync_medical_records_to_blockchain)
            except Exception as e:
                logging.error(f"Erro no worker de sincronização blockchain: {e}")
            
            # Aguarda 1 hora antes da próxima execução
            await asyncio.sleep(3600)

    # Inicia a tarefa em segundo plano
    sync_task = asyncio.create_task(blockchain_sync_worker())
    
    yield
    
    # Finalização: cancela a tarefa ao desligar a aplicação
    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="MediVault API",
        description="API para gerenciamento de registros medicos com verificacao blockchain",
        version="1.0.0",
        lifespan=lifespan,
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
    app.include_router(blockchain_router, prefix="/api/v1/blockchain")

    return app


# Create application instance
app = create_app()
