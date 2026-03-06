import uuid
import jwt

from passlib.hash import pbkdf2_sha256
from app.settings import settings


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    return pbkdf2_sha256.verify(password, password_hash)


def check_password(hash, password):
    """Verifica se uma senha e valido a partir de um algoritmo de hash."""
    return pbkdf2_sha256.verify(password, hash)


def make_password(password):
    """Gera uma senha a partir de um algoritmo de hash."""
    return pbkdf2_sha256.hash(password)


generate_passwd_hash = make_password  # alias para compatibilidade


def get_session_name(session_key):
    """Gera um identificador unico da sessao dentro de um cache."""
    return "auth.session.{}".format(session_key)


def encode_jwt(obj):
    """Converte um dicionario para um token JWT."""
    token = jwt.encode(obj, settings.SECRET_KEY, algorithm="HS256")
    return token.decode("utf-8")


def decode_jwt(token):
    """Converte um token JWT para um dicionario."""
    obj = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"verify_exp": True},
    )
    return obj


decode_token = decode_jwt  # alias


def create_access_token(
    user_data: dict,
    refresh: bool = False,
    expiry_seconds: int = None,
) -> str:
    """Cria token JWT com dados do usuario."""
    import datetime
    expiry = expiry_seconds or (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=expiry)
    payload = {
        "user": user_data,
        "email": user_data.get("email"),
        "profile_role_group_active": user_data.get("role"),
        "sub": user_data.get("user_uid"),
        "exp": exp,
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_url_safe_token(data: dict) -> str:
    """Cria token para links (verificacao, reset senha)."""
    import datetime
    payload = {
        **data,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_url_safe_token(token: str) -> dict | None:
    """Decodifica token de link."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except Exception:
        return None
