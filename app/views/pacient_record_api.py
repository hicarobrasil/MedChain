from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from app.database import get_db
from app.service.pacient_record_service import PacientService
from sqlalchemy.orm import Session
from app.models.pacient_record import GENDER_MAP, STATUS_MAP

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
    id: int
    name: str
    dateofbirth: date
    gender: str  # Retorna como string
    email: EmailStr
    phone: str
    status: str  # Retorna como string
    date_created: datetime
    date_updated: Optional[datetime] = None

    class Config:
        orm_mode = True
        
    # Método para converter de ORM para response model
    @classmethod
    def from_orm(cls, obj):
        # Cria uma cópia do objeto
        dict_obj = {
            "id": obj.id,
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

router = APIRouter()

@router.post("/pacients", response_model=PacientResponse, status_code=status.HTTP_201_CREATED)
async def create_pacient(
    name: str = Form(...),
    dateofbirth: date = Form(...),
    gender: int = Form(...), 
    email: EmailStr = Form(...),
    phone: str = Form(...),
    status: int = Form(...), 
    db: Session = Depends(get_db)
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
    # Converte manualmente para o formato de resposta
    return PacientResponse.from_orm(pacient)

@router.get("/pacients/{pacient_id}", response_model=PacientResponse)
def get(pacient_id: int, db: Session = Depends(get_db)):
    service = PacientService(db)
    pacient = service.get_pacient_by_id(pacient_id)
    # Converte manualmente para o formato de resposta
    return PacientResponse.from_orm(pacient)

@router.get("/pacients", response_model=list[PacientResponse])
def list_all(db: Session = Depends(get_db)):
    service = PacientService(db)
    pacients = service.get_all_pacients()
    # Converte cada paciente para o formato de resposta
    return [PacientResponse.from_orm(p) for p in pacients]

@router.put("/pacients/{pacient_id}", response_model=PacientResponse)
def update(pacient_id: int, update_data: PacientUpdate, db: Session = Depends(get_db)):
    service = PacientService(db)
    pacient = service.update_pacient(pacient_id, update_data.dict(exclude_unset=True))
    # Converte manualmente para o formato de resposta
    return PacientResponse.from_orm(pacient)

@router.delete("/pacients/{pacient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(pacient_id: int, db: Session = Depends(get_db)):
    service = PacientService(db)
    service.delete_pacient(pacient_id)
    return {"detail": "Paciente deletado com sucesso"}