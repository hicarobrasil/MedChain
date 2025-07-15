from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.doctor.service import DoctorService
from app.doctor.schemas import DoctorCreate, DoctorUpdate, DoctorOut
from app.auth.dependencies import get_current_user, RoleChecker
from app.models.login_record import User
from app.errors import UserNotFound

doctor_router = APIRouter(prefix="/doctors", tags=["doctors"])
doctor_service = DoctorService()

# Verificadores de permissão
admin_role = RoleChecker(["admin"])
admin_or_doctor_role = RoleChecker(["admin", "doctor"])

@doctor_router.post("/", status_code=status.HTTP_201_CREATED, response_model=DoctorOut)
def create_doctor(
    doctor_data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_role),
):
    """Cria um novo médico (apenas admin)"""
    
    # Verificar se CRM já existe
    if doctor_service.doctor_exists(doctor_data.crm, db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CRM já está em uso"
        )
    
    # Verificar se email já existe
    if doctor_service.email_exists(doctor_data.email, db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já está em uso"
        )
    
    try:
        new_doctor = doctor_service.create_doctor(doctor_data, db)
        return new_doctor
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@doctor_router.get("/", response_model=List[DoctorOut])
def list_doctors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    specialty: str = Query(None, description="Filtrar por especialidade"),
    active_only: bool = Query(False, description="Apenas médicos ativos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_doctor_role),
):
    """Lista médicos com filtros opcionais"""
    
    if specialty:
        doctors = doctor_service.get_doctors_by_specialty(specialty, db)
    elif active_only:
        doctors = doctor_service.get_active_doctors(db)
    else:
        doctors = doctor_service.get_all_doctors(skip=skip, limit=limit, db=db)
    
    return doctors

@doctor_router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(
    doctor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_doctor_role),
):
    """Busca um médico pelo ID"""
    
    doctor = doctor_service.get_doctor_by_id(doctor_id, db)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Médico não encontrado"
        )
    
    return doctor

@doctor_router.get("/crm/{crm}", response_model=DoctorOut)
def get_doctor_by_crm(
    crm: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_doctor_role),
):
    """Busca um médico pelo CRM"""
    
    doctor = doctor_service.get_doctor_by_crm(crm, db)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Médico não encontrado"
        )
    
    return doctor

@doctor_router.put("/{doctor_id}", response_model=DoctorOut)
def update_doctor(
    doctor_id: UUID,
    doctor_data: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_role),
):
    """Atualiza dados de um médico (apenas admin)"""
    
    doctor = doctor_service.get_doctor_by_id(doctor_id, db)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Médico não encontrado"
        )
    
    # Verificar se novo CRM não está em uso
    if doctor_data.crm and doctor_data.crm != doctor.crm:
        if doctor_service.doctor_exists(doctor_data.crm, db):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="CRM já está em uso"
            )
    
    # Verificar se novo email não está em uso
    if doctor_data.email and doctor_data.email != doctor.email:
        if doctor_service.email_exists(doctor_data.email, db):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email já está em uso"
            )
    
    try:
        updated_doctor = doctor_service.update_doctor(doctor, doctor_data, db)
        return updated_doctor
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@doctor_router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(
    doctor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_role),
):
    """Remove um médico (apenas admin)"""
    
    doctor = doctor_service.get_doctor_by_id(doctor_id, db)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Médico não encontrado"
        )
    
    success = doctor_service.delete_doctor(doctor, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao remover médico"
        )
