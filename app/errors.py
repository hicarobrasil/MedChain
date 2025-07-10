
from fastapi import HTTPException, status

class InvalidCredentials(HTTPException):
    def __init__(self, detail: str = "Credenciais inválidas"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

class UserAlreadyExists(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Usuário já existe",
        )

class UserNotFound(HTTPException):
    def __init__(self, detail: str = "Usuário não encontrado"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

class InvalidToken(HTTPException):
    def __init__(self, detail: str = "Token inválido ou expirado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

class AccessTokenRequired(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token é necessário",
        )

class RefreshTokenRequired(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token é necessário",
        )

class InsufficientPermission(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente",
        )

class AccountNotVerified(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta não verificada",
        )