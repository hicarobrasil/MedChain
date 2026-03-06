from abc import ABCMeta, abstractproperty
from collections import UserDict
from enum import Enum
from typing import Union

from jwt import ExpiredSignatureError, InvalidTokenError

from app.auth.service import SessionDataSource
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


class UserRole(str, Enum):
    ADMIN = "ADMN"
    DOCTOR = "DOCT"
    PATIENT = "PACI"


class User(metaclass=ABCMeta):
    email: str
    session: UserDict = UserDict({}, access_token=None)

    @abstractproperty
    def is_authenticated(self):
        raise NotImplementedError

    @abstractproperty
    def role(self):
        raise NotImplementedError


class AuthenticatedUser(User):
    """Usuario autenticado a partir de uma sessao salva.

    Attributes:
        email (obj): Email do usuario (identificador da sessao).
        session (obj): Dicionario de dados da sessao.
    """

    def __init__(self, email, session=None, token_acesso=None):
        self.email = email
        self.session = UserDict(session or {}, access_token=token_acesso)

    @property
    def is_authenticated(self):
        return True

    @property
    def role(self) -> Union[UserRole, None]:
        return (
            UserRole(self.session["profile_role_group_active"])
            if self.session["profile_role_group_active"]
            else None
        )

    @property
    def token(self):
        return self.session["access_token"]

    @property
    def uuid(self) -> str:
        return self.session["sub"]


class AnonymousUser(User):
    """Usuario anônimo."""

    @property
    def is_authenticated(self):
        return False

    @property
    def role(self) -> None:
        return None


async def get_user(acess_token: str = Depends(api_key_header)) -> User:
    """Busca o usuario autenticado.

    Utiliza o protocolo "Bearer Token" e um token de acesso especificado
    no header `Authorization` para processar os dados de autenticacao.
    """

    if acess_token:
        acess_token = acess_token.split("Bearer ")[-1]
    else:
        raise HTTPException(status_code=401, detail="Nao autenticado.")

    if isinstance(acess_token, type(None)) or not acess_token:
        raise HTTPException(status_code=401, detail="Nao autenticado.")

    try:
        session_data = SessionDataSource().get_token(acess_token)
        email = session_data["email"]
        return AuthenticatedUser(email, session_data, token_acesso=acess_token)
    except (ExpiredSignatureError, InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Nao autenticado.")
