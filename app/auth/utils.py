import jwt

from passlib.hash import pbkdf2_sha256
from settings import settings



def check_password(hash, password):
    """Verifica se uma senha é valido a partir de um algoritmo de hash."""
    return pbkdf2_sha256.verify(password, hash)


def make_password(password):
    """Gera uma senha a partir de um algoritmo de hash."""
    return pbkdf2_sha256.hash(password)


def get_session_name(session_key):
    """Gera um identificador único da sessão dentro de um cache."""
    return "auth.session.{}".format(session_key)


def encode_jwt(obj):
    """Converte um dicionário para um token JWT."""
    token = jwt.encode(obj, settings.SECRET_KEY, algorithm="HS256")
    return token.decode("utf-8")


def decode_jwt(token):
    """Converte um token JWT para um dicionário."""
    obj = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        options={
            "verify_exp": True,
        },
    )

    return obj
