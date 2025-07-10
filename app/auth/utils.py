import logging
from typing import Optional
import uuid
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer

from jose import jwt, JWTError
from passlib.context import CryptContext
from app.settings import Settings

settings = Settings()

# Configuração específica para bcrypt
passwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12
)

def generate_passwd_hash(password: str) -> str:
    return passwd_context.hash(password)

def verify_password(password: str, hash_str: str) -> bool:
    return passwd_context.verify(password, hash_str)

def create_access_token(
    user_data: dict, expiry_seconds: int = None, refresh: bool = False
) -> str:
    try:
        
        expires_in = expiry_seconds or settings.ACCESS_TOKEN_EXPIRE_SECONDS
        exp_time = datetime.utcnow() + timedelta(seconds=expires_in)
        
     
        serializable_user_data = {}
        for key, value in user_data.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                serializable_user_data[key] = value
            else:
               
                serializable_user_data[key] = str(value)

        
        payload = {
            "user": serializable_user_data,
            "exp": int(exp_time.timestamp()),
            "jti": str(uuid.uuid4()),
            "refresh": refresh,
            "iat": int(datetime.utcnow().timestamp()),
        }

     
        logging.debug(f"JWT Payload antes da codificação: {payload}")

        token = jwt.encode(
            payload, 
            settings.JWT_SECRET, 
            algorithm=settings.JWT_ALGORITHM
        )

      
        if isinstance(token, str) and token.count('.') == 2:
            logging.debug("Token JWT gerado com sucesso.")
        else:
            logging.error("Formato do token JWT gerado não está correto.")
            raise ValueError("Falha na geração do token JWT")

        return token
        
    except Exception as e:
        logging.error(f"Erro ao criar access token: {str(e)}")
        raise
def decode_token(token: str) -> Optional[dict]:
    try:
        
        if not isinstance(token, str):
            logging.error("Token inválido: não é uma string")
            return None
            
        if not token or token.isspace():
            logging.error("Token vazio ou só com espaços")
            return None
            
        
        if token.count('.') != 2:
            logging.error("Token não tem o formato JWT válido")
            return None
        
        logging.debug(f"Decodificando token JWT: {token[:20]}...")
        
        token_data = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        if not token_data or "user" not in token_data:
            logging.error("Token não contém payload válido")
            return None
            
        exp = token_data.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            logging.error("Token expirado")
            return None
            
        return token_data
        
    except JWTError as e:
        logging.error(f"Erro ao decodificar JWT: {str(e)}")
        return None
    except ValueError as e:
        logging.error(f"Erro de valor ao decodificar JWT: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao decodificar JWT: {str(e)}")
        return None

serializer = URLSafeTimedSerializer(
    secret_key=settings.JWT_SECRET, salt="email-verification"
)

def create_url_safe_token(data: dict) -> str:
    return serializer.dumps(data)

def decode_url_safe_token(token: str, max_age: int = 86400) -> Optional[dict]:
    try:
        token_data = serializer.loads(token, max_age=max_age)
        return token_data
    except Exception as e:
        logging.error(f"Error decoding URL safe token: {str(e)}")
        return None