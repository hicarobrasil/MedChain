import uuid
from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from app.database import get_db
from app.service.pacient_record_service import PacientService
from sqlalchemy.orm import Session
from app.models.patient import GENDER_MAP, STATUS_MAP
from app.dependencies import token_auth, admin_only, user_or_admin, verify_patient_access

class PacientCreate(BaseModel):
    name: str
    dateofbirth: date
    gender: int 
    email: EmailStr
    phone: str
    status: int  

class PacientUpdate(BaseModel):
    name: Optional[str]
    dateofbirth: Optional[date]
    gender: Optional[int] 
    email: Optional[EmailStr]
    phone: Optional[str]
    status: Optional[int] 

class PacientResponse(BaseModel):
    uid: uuid.UUID
    name: str
    dateofbirth: date
    gender: str  
    email: EmailStr
    phone: str
    status: str  
    date_created: datetime
    date_updated: Optional[datetime] = None

    class Config:
        orm_mode = True
        
        
    @classmethod
    def from_orm(cls, obj):
        dict_obj = {
            "uid": obj.uid,
            "name": obj.name,
            "dateofbirth": obj.dateofbirth,
            "gender": GENDER_MAP[obj.gender],  
            "email": obj.email,
            "phone": obj.phone,
            "status": STATUS_MAP[obj.status],  
            "date_created": obj.date_created,
            "date_updated": obj.date_updated,
        }
        return cls(**dict_obj)

router = APIRouter(tags=["Pacient"])

@router.post("/pacients", response_model=PacientResponse, status_code=status.HTTP_201_CREATED)
async def create_pacient(
    name: str = Form(...),
    dateofbirth: date = Form(...),
    gender: int = Form(...), 
    email: EmailStr = Form(...),
    phone: str = Form(...),
    status: int = Form(...), 
    db: Session = Depends(get_db),
    _: bool = Depends(admin_only)  # Apenas admin pode criar pacientes
):
    service = PacientService(db)
    data = {
        "name": name,
        "dateofbirth": dateofbirth,
        "gender": gender,  
        "email": email,
        "phone": phone,
        "status": status  
    }
    pacient = service.create_pacient(data)
    return PacientResponse.from_orm(pacient)

@router.get("/pacients/{pacient_uid}", response_model=PacientResponse)
async def get_pacient(
    pacient_uid: uuid.UUID, 
    db: Session = Depends(get_db),
    _: bool = Depends(verify_patient_access)  # Verifica se o usuário tem acesso ao paciente
):
    service = PacientService(db)
    pacient = service.get_pacient_by_uid(pacient_uid)
    return PacientResponse.from_orm(pacient)

@router.get("/pacients", response_model=list[PacientResponse])
async def list_all_pacients(
    db: Session = Depends(get_db),
    _: bool = Depends(admin_only)  # Apenas admin pode listar todos os pacientes
):
    service = PacientService(db)
    pacients = service.get_all_pacients()
    return [PacientResponse.from_orm(p) for p in pacients]

@router.put("/pacients/{pacient_uid}", response_model=PacientResponse)
async def update_pacient(
    pacient_uid: uuid.UUID,
    name: str = Form(...),
    dateofbirth: str = Form(...),
    gender: int = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    status: int = Form(...),
    db: Session = Depends(get_db),
    _: bool = Depends(admin_only)  # Apenas admin pode atualizar pacientes
):
    service = PacientService(db)

    try:
        dob = datetime.fromisoformat(dateofbirth)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido")

    update_data = {
        "name": name,
        "dateofbirth": dob,
        "gender": gender,
        "email": email,
        "phone": phone,
        "status": status
    }

    pacient = service.update_pacient(pacient_uid, update_data)
    return PacientResponse.from_orm(pacient)

@router.delete("/pacients/{pacient_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pacient(
    pacient_uid: uuid.UUID, 
    db: Session = Depends(get_db),
    _: bool = Depends(admin_only)  # Apenas admin pode deletar pacientes
):
    service = PacientService(db)
    service.delete_pacient(pacient_uid)
    return {"detail": "Paciente deletado com sucesso"}
