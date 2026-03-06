
from fastapi import HTTPException, status

class InvalidCredentials(HTTPException):
    def __init__(self, detail: str = "Credenciais invalidas"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

class UserAlreadyExists(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Usuario ja existe",
        )

class UserNotFound(HTTPException):
    def __init__(self, detail: str = "Usuario nao encontrado"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

class InvalidToken(HTTPException):
    def __init__(self, detail: str = "Token invalido ou expirado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

class AccessTokenRequired(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token e necessario",
        )

class RefreshTokenRequired(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token e necessario",
        )

class InsufficientPermission(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissao insuficiente",
        )

class AccountNotVerified(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta nao verificada",
        )