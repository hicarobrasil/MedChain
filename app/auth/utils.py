import logging
from typing import Optional
import uuid
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer

import jwt
from passlib.context import CryptContext

from app.settings import Settings

settings = Settings()

passwd_context = CryptContext(schemes=["bcrypt"])

def generate_passwd_hash(password: str) -> str:
    return passwd_context.hash(password)

def verify_password(password: str, hash_str: str) -> bool:
    return passwd_context.verify(password, hash_str)

def create_access_token(
    user_data: dict, expiry: timedelta = None, refresh: bool = False
) -> str:
    payload = {
        "user": user_data,
        "exp": datetime.utcnow() + (
            expiry if expiry is not None else timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        ),
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(
        payload=payload, 
        key=settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )

    return token

def decode_token(token: str) -> Optional[dict]:
    try:
        token_data = jwt.decode(
            jwt=token, 
            key=settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return token_data
    except jwt.PyJWTError as e:
        logging.exception(e)
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