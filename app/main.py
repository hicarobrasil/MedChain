# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from app.views.medical_record_api import router as medical_records_router

# def create_app() -> "FastAPI":
    
#     app = FastAPI(
#         title="MediVault API",
#         description="API para gerenciamento de registros médicos com verificação blockchain",
#         version="1.0.0"
#     )
    
#     # Configurar CORS
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=["*"],  # Em produção, especificar origens permitidas
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
    
#     # Registrar rotas
#     app.include_router(medical_records_router, prefix="/api/v1")

    
#     return app

# # if __name__ == "__main__":
# #     import uvicorn
# #     uvicorn.run("main:create_app", host="127.0.0.1", port=8000, reload=True, factory=True)

# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# def read_root():
#     return {"message": "Hello, FastAPI"}
