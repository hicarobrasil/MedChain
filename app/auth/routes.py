from fastapi import APIRouter
from app.settings import get_settings
from app.auth.dependencies import RoleChecker
from app.auth.service import UserService
from app.auth.utils import (
    create_access_token,
    decode_url_safe_token,
    generate_passwd_hash,
    verify_password,
    create_url_safe_token
)

from app.auth.schemas import (
    UserCreateModel,
    UserLoginModel,
    DoctorRegisterModel,
    DoctorCompleteModel,
    PasswordResetRequestModel,
    PasswordResetConfirmModel,
    TokenResponse,
)
from app.database.redis import RedisClient
from app.database import get_db
from app.models.login_record import User
from app.errors import (
    UserAlreadyExists,
    UserNotFound,
    InvalidToken,
    InvalidCredentials,
)
from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import logging
from app.auth.dependencies import AccessTokenBearer, RefreshTokenBearer, get_current_user
from app.auth.utils import make_password
from app.models.user import UserModel, StatusEnum
from app.models.doctor import DoctorModel
from app.models.doctor import SpecialtyEnum as DoctorSpecialtyEnum
from app.models.patient import PatientModel

auth_router = APIRouter(prefix="/auth", tags=["auth"])
user_service = UserService()
settings = get_settings()
redis_client = RedisClient() 

admin_role = RoleChecker(["admin"])
user_or_admin_role = RoleChecker(["admin", "user"])

SPECIALTY_MAP = {
    "clínica geral": "GENERAL",
    "clinica geral": "GENERAL",
    "cardiologia": "CARDIOLOGY",
    "dermatologia": "DERMATOLOGY",
    "neurologia": "NEUROLOGY",
    "pediatria": "PEDIATRICS",
    "psiquiatria": "PSYCHIATRY",
    "ortopedia": "ORTHOPEDICS",
}


def _resolve_specialty(specialty_str: str) -> DoctorSpecialtyEnum:
    """Converte string de especialidade para enum, com fallback para OTHER."""
    s = (specialty_str or "").strip()
    key = s.lower()
    value = SPECIALTY_MAP.get(key) or s.upper().replace(" ", "_").replace("Í", "I") or "OTHER"
    try:
        return DoctorSpecialtyEnum(value)
    except ValueError:
        return DoctorSpecialtyEnum.OTHER


def send_verification_email(email: str, username: str, token: str):
    """Funcao para enviar email de verificacao"""
    link = f"http://{settings.DOMAIN}/api/v1/auth/verify/{token}"
    
    html = f"""
    <h1>Ola {username}, verifique seu email</h1>
    <p>Por favor, clique neste <a href="{link}">link</a> para verificar seu email.</p>
    <p>O link e valido por 24 horas.</p>
    """
    
    subject = "Verifique seu email"
    
    logging.info(f"Email de verificacao enviado para {email}")


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_user_account(
    user_data: UserCreateModel,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Cria uma nova conta de usuario"""
    email = user_data.email

    if user_service.user_exists(email, db):
        raise UserAlreadyExists()

    new_user = user_service.create_user(user_data, db)

    token = create_url_safe_token({"email": email})
    
    background_tasks.add_task(
        send_verification_email, 
        email=email,
        username=user_data.username,
        token=token
    )

    return {
        "message": "Conta criada com sucesso! Verifique seu email para ativar sua conta.",
        "user": {
            "uid": str(new_user.uid),
            "username": new_user.username,
            "email": new_user.email,
        }
    }


@auth_router.post("/register-doctor", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
def register_doctor(
    data: DoctorRegisterModel,
    db: Session = Depends(get_db),
):
    """Cadastro de medico: cria auth_users (login) + users/doctor (dados do app)."""
    try:
        if user_service.user_exists(data.email, db):
            raise UserAlreadyExists()
        auth_user = user_service.create_user(
            UserCreateModel(username=data.email, email=data.email, password=data.password),
            db,
        )
        user_service.update_user(auth_user, {"role": "doctor", "is_verified": True}, db)
        app_user = UserModel(
            full_name=data.full_name,
            email=data.email,
            password=make_password(data.password),
            status=StatusEnum.ACTIVE,
        )
        db.add(app_user)
        db.commit()
        db.refresh(app_user)
        specialty = _resolve_specialty(data.specialty)
        doctor = DoctorModel(
            CRM=data.CRM,
            specialty=specialty,
            user_id=app_user.id,
        )
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
    except UserAlreadyExists:
        raise
    except Exception as e:
        logging.exception("Erro ao cadastrar médico")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao cadastrar: {str(e)}. Verifique se o banco de dados está rodando.",
        )
    access_token = create_access_token(
        user_data={
            "email": auth_user.email,
            "user_uid": str(auth_user.uid),
            "role": "doctor",
        }
    )
    refresh_token = create_access_token(
        user_data={"email": auth_user.email, "user_uid": str(auth_user.uid)},
        refresh=True,
        expiry_seconds=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(doctor.public_id),
            "uid": str(auth_user.uid),
            "email": auth_user.email,
            "username": auth_user.username,
            "full_name": data.full_name,
            "is_verified": True,
            "role": "doctor",
            "type": "doctor",
            "public_id": str(doctor.public_id),
        },
    }


@auth_router.get("/verify/{token}", status_code=status.HTTP_200_OK)
def verify_user_account(token: str, db: Session = Depends(get_db)):
    """Verifica a conta do usuario atraves do token enviado por email"""
    token_data = decode_url_safe_token(token)
    
    if not token_data:
        raise InvalidToken()

    user_email = token_data.get("email")
    
    if not user_email:
        raise InvalidToken()

    user = user_service.get_user_by_email(user_email, db)
    
    if not user:
        raise UserNotFound()
        
    if user.is_verified:
        return {"message": "Conta ja verificada anteriormente"}

    user_service.update_user(user, {"is_verified": True}, db)
    
    return {"message": "Conta verificada com sucesso"}

@auth_router.post("/verify-account/{email}", status_code=status.HTTP_200_OK)
def verify_account_manual(email: str, db: Session = Depends(get_db)):
    """Verifica a conta do usuario manualmente (apenas para testes)"""
    user = user_service.get_user_by_email(email, db)
    
    if not user:
        raise UserNotFound()
        
    if user.is_verified:
        return {"message": "Conta ja verificada anteriormente"}

    user_service.update_user(user, {"is_verified": True}, db)
    
    return {"message": "Conta verificada com sucesso"}


@auth_router.get("/fix-doctor-roles", status_code=status.HTTP_200_OK)
def fix_doctor_roles(db: Session = Depends(get_db)):
    """
    Corrige role em auth_users: define role='doctor' para emails que têm DoctorModel.
    Chame: GET /api/v1/auth/fix-doctor-roles
    """
    updated = []
    for doctor in db.query(DoctorModel).join(UserModel, DoctorModel.user_id == UserModel.id).all():
        email = doctor.user.email
        auth_user = user_service.get_user_by_email(email, db)
        if auth_user and (auth_user.role or "").lower() != "doctor":
            user_service.update_user(auth_user, {"role": "doctor"}, db)
            updated.append(email)
    return {"message": "Concluído", "updated": updated, "count": len(updated)}


@auth_router.post("/complete-doctor", status_code=status.HTTP_200_OK)
def complete_doctor_registration(data: DoctorCompleteModel, db: Session = Depends(get_db)):
    """
    Completa cadastro de médico quando o usuário já existe em auth_users mas não tem UserModel/DoctorModel.
    Cria users + doctor e atualiza auth_users.role para 'doctor'.
    POST /api/v1/auth/complete-doctor com body: {"email":"...","full_name":"...","CRM":"...","specialty":"..."}
    """
    auth_user = user_service.get_user_by_email(data.email, db)
    if not auth_user:
        raise UserNotFound()
    app_user = db.query(UserModel).filter(func.lower(UserModel.email) == data.email.lower()).first()
    if app_user:
        doctor = db.query(DoctorModel).filter(DoctorModel.user_id == app_user.id).first()
        if doctor:
            raise HTTPException(status_code=400, detail="Este email já está cadastrado como médico.")
        raise HTTPException(status_code=400, detail="Este email já existe como paciente. Use outro email.")
    # Criar UserModel e DoctorModel
    app_user = UserModel(
        full_name=data.full_name,
        email=data.email,
        password=make_password("temp"),  # não usado para login
        status=StatusEnum.ACTIVE,
    )
    db.add(app_user)
    db.commit()
    db.refresh(app_user)
    specialty = _resolve_specialty(data.specialty)
    doctor = DoctorModel(CRM=data.CRM, specialty=specialty, user_id=app_user.id)
    db.add(doctor)
    db.commit()
    user_service.update_user(auth_user, {"role": "doctor", "is_verified": True}, db)
    return {"message": "Cadastro de médico concluído. Faça login novamente.", "email": data.email}


@auth_router.get("/check-role", status_code=status.HTTP_200_OK)
def check_user_role(email: str, db: Session = Depends(get_db)):
    """
    Diagnóstico: verifica auth_users, users, doctor para um email.
    Chame: GET /api/v1/auth/check-role?email=dinizkaroline1@gmail.com
    """
    email = (email or "").strip()
    email_lower = email.lower()
    auth_user = user_service.get_user_by_email(email, db) or user_service.get_user_by_email(email_lower, db)
    app_user = db.query(UserModel).filter(func.lower(UserModel.email) == email_lower).first()
    doctor = db.query(DoctorModel).filter(DoctorModel.user_id == app_user.id).first() if app_user else None
    patient = db.query(PatientModel).filter(PatientModel.user_id == app_user.id).first() if app_user else None
    resolved = _resolve_user_role(email_lower, (auth_user.role or "") if auth_user else "", db)
    return {
        "email": email_lower,
        "auth_users": {"exists": auth_user is not None, "role": getattr(auth_user, "role", None) if auth_user else None},
        "users": {"exists": app_user is not None},
        "doctor": {"exists": doctor is not None},
        "patient": {"exists": patient is not None},
        "resolved_role": resolved,
    }


def _resolve_user_role(email: str, auth_role: str, db: Session) -> str:
    """Deriva o role real: doctor, patient ou admin conforme auth_role e dados em users/doctor/patient."""
    if auth_role and str(auth_role).lower() == "doctor":
        return "doctor"
    if auth_role and str(auth_role).lower() == "patient":
        return "patient"
    email_lower = (email or "").strip().lower()
    if not email_lower:
        return auth_role if auth_role in ("doctor", "patient", "admin") else "patient"
    app_user = db.query(UserModel).filter(func.lower(UserModel.email) == email_lower).first()
    if not app_user:
        return auth_role if auth_role in ("doctor", "patient", "admin") else "patient"
    doctor = db.query(DoctorModel).filter(DoctorModel.user_id == app_user.id).first()
    patient = db.query(PatientModel).filter(PatientModel.user_id == app_user.id).first()
    if doctor:
        return "doctor"
    if patient:
        return "patient"
    return auth_role if auth_role in ("doctor", "patient", "admin") else "patient"


@auth_router.post("/login", response_model=TokenResponse)
def login_user(
    login_data: UserLoginModel, 
    db: Session = Depends(get_db)
):
    """Autentica o usuario e retorna tokens de acesso"""
    email = login_data.email
    password = login_data.password

    user = user_service.get_user_by_email(email, db)
    
    if not user:
        raise InvalidCredentials()

    if not verify_password(password, user.password_hash):
        raise InvalidCredentials()

    role = _resolve_user_role(email, user.role or "", db)
    public_id = None
    patient_public_id = None
    email_lower = (email or "").strip().lower()
    app_user = db.query(UserModel).filter(func.lower(UserModel.email) == email_lower).first()
    if app_user:
        if role == "doctor":
            doctor = db.query(DoctorModel).filter(DoctorModel.user_id == app_user.id).first()
            if doctor:
                public_id = str(doctor.public_id)
        elif role == "patient":
            patient = db.query(PatientModel).filter(PatientModel.user_id == app_user.id).first()
            if patient:
                patient_public_id = str(patient.public_id)
        
    access_token = create_access_token(
        user_data={
            "email": user.email,
            "user_uid": str(user.uid),
            "role": role,
        }
    )

    refresh_token = create_access_token(
        user_data={
            "email": user.email,
            "user_uid": str(user.uid),
        },
        refresh=True,
        expiry_seconds=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # converter dias para segundos
    )

    user_payload = {
        "uid": str(user.uid),
        "email": user.email,
        "username": user.username,
        "is_verified": user.is_verified,
        "role": role,
    }
    if public_id:
        user_payload["id"] = public_id
        user_payload["public_id"] = public_id
    if patient_public_id:
        user_payload["patient_public_id"] = patient_public_id

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_payload,
    }

@auth_router.post("/refresh-token", response_model=dict)
def refresh_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    """Gera um novo access token a partir de um refresh token valido"""
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) < datetime.utcnow():
        raise InvalidToken()

    new_access_token = create_access_token(user_data=token_details["user"])

    return {"access_token": new_access_token}

@auth_router.post("/logout", status_code=status.HTTP_200_OK)
def logout_user(token_details: dict = Depends(AccessTokenBearer())):
    """Revoga o token atual adicionando-o à blacklist"""
    jti = token_details["jti"]
    
    expiry = token_details["exp"]
    ttl = expiry - int(datetime.utcnow().timestamp())
    
    redis_client.add_token_to_blacklist(jti, ttl)
    
    return {"message": "Logout realizado com sucesso"}

@auth_router.get("/me", response_model=dict)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Retorna informacoes do usuario atual"""
    return {
        "uid": str(current_user.uid),
        "username": current_user.username,
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "role": current_user.role,
        "date_created": current_user.date_created.isoformat(),
        "date_updated": current_user.date_updated.isoformat(),
    }

@auth_router.post("/reset-password-request", status_code=status.HTTP_200_OK)
def request_password_reset(
    reset_request: PasswordResetRequestModel,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Solicita redefinicao de senha enviando um email com um link"""
    email = reset_request.email
    
    user = user_service.get_user_by_email(email, db)
    
    if not user:
        return {"message": "Se o email existir no sistema, você recebera instrucoes para redefinir sua senha."}
    
    token = create_url_safe_token({"email": email, "type": "password_reset"})
    
    link = f"http://{settings.DOMAIN}/reset-password/{token}"
    
    html = f"""
    <h1>Redefinicao de Senha</h1>
    <p>Ola {user.username},</p>
    <p>Você solicitou a redefinicao de sua senha. Clique no <a href="{link}">link</a> para definir uma nova senha.</p>
    <p>O link e valido por 24 horas.</p>
    <p>Se você nao solicitou essa redefinicao, por favor ignore este email.</p>
    """
    
    subject = "Redefinicao de Senha"
    logging.info(f"Email de redefinicao de senha enviado para {email}")
    
    return {"message": "Se o email existir no sistema, você recebera instrucoes para redefinir sua senha."}

@auth_router.post("/reset-password/{token}", status_code=status.HTTP_200_OK)
def reset_password(
    token: str,
    password_data: PasswordResetConfirmModel,
    db: Session = Depends(get_db),
):
    """Redefine a senha do usuario utilizando o token recebido por email"""
    if password_data.new_password != password_data.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="As senhas nao coincidem",
        )
    
    token_data = decode_url_safe_token(token)
    
    if not token_data:
        raise InvalidToken()
        
    email = token_data.get("email")
    reset_type = token_data.get("type")
    
    if not email or reset_type != "password_reset":
        raise InvalidToken()
    
    user = user_service.get_user_by_email(email, db)
    
    if not user:
        raise UserNotFound()
    
    password_hash = generate_passwd_hash(password_data.new_password)
    user_service.update_user(user, {"password_hash": password_hash}, db)
    
    return {"message": "Senha redefinida com sucesso"}