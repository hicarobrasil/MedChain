from fastapi import Depends, HTTPException, status
from uuid import UUID
from app.auth.dependencies import AccessTokenBearer, RoleChecker
from app.service.medical_record_service import MedicalRecordService
from app.service.pacient_record_service import PacientService
from app.database import get_db
from sqlalchemy.orm import Session

# Authentication dependencies
token_auth = AccessTokenBearer()
admin_only = RoleChecker(["admin"])
user_or_admin = RoleChecker(["user", "admin"])

# Medical records access control
async def verify_record_access(
    record_id: int,
    token_data: dict = Depends(token_auth),
    db: Session = Depends(get_db)
) -> bool:
    """Verifica se o usuario tem acesso ao registro medico."""
    service = MedicalRecordService(db)
    record = service.get_medical_record(record_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro medico nao encontrado"
        )
    
    # Admins têm acesso a todos os registros
    if "admin" in token_data.get("role", []):
        return True
        
    user_id = token_data.get("user_uid")
    
    # Verifica se o usuario e o paciente ou o medico do registro
    is_patient = str(record.patient_id) == user_id
    is_doctor = record.doctor_id == user_id
    
    if not (is_patient or is_doctor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissao para acessar este registro"
        )
    
    return True

async def verify_patient_records_access(
    patient_id: UUID,
    token_data: dict = Depends(token_auth),
    db: Session = Depends(get_db)
) -> bool:
    """Verifica se o usuario tem acesso aos registros do paciente."""
    # Admins têm acesso a todos os registros
    if "admin" in token_data.get("role", []):
        return True
        
    user_id = token_data.get("user_uid")
    
    # Verifica se o usuario e o proprio paciente
    if str(patient_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissao para acessar registros deste paciente"
        )
    
    return True

async def verify_doctor_records_access(
    doctor_id: str,
    token_data: dict = Depends(token_auth),
    db: Session = Depends(get_db)
) -> bool:
    """Verifica se o usuario tem acesso aos registros do medico."""
    # Admins têm acesso a todos os registros
    if "admin" in token_data.get("role", []):
        return True
        
    user_id = token_data.get("user_uid")
    
    # Verifica se o usuario e o proprio medico
    if doctor_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissao para acessar registros deste medico"
        )
    
    return True

# Patient access control
async def verify_patient_access(
    patient_uid: UUID,
    token_data: dict = Depends(token_auth),
    db: Session = Depends(get_db)
) -> bool:
    """Verifica se o usuario tem acesso ao paciente."""
    # Admins têm acesso a todos os pacientes
    if "admin" in token_data.get("role", []):
        return True
        
    user_id = token_data.get("user_uid")
    
    # Verifica se o usuario e o proprio paciente
    if str(patient_uid) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissao para acessar este paciente"
        )
    
    return True

