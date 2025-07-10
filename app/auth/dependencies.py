from typing import Any, List

from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db as get_session
from app.errors import AccessTokenRequired, InvalidToken, RefreshTokenRequired, UserNotFound, InsufficientPermission, AccountNotVerified
from app.models.login_record import User
from app.database.redis import RedisClient

from .service import UserService
from .utils import decode_token

user_service = UserService()
redis_client = RedisClient()  # Instanciar o cliente Redis

class TokenBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict:
        try:
            credentials = await super().__call__(request)
            
            if not credentials:
                raise InvalidToken("Credenciais não fornecidas")

            token = credentials.credentials
            
            if not token:
                raise InvalidToken("Token não fornecido")
            
            import logging
            if token.startswith('"') and token.endswith('"'):
                logging.error(f"Token com aspas detectado: {token[:30]}...")
                raise InvalidToken("Token contém aspas - remova as aspas do header Authorization")
            
            if not token or token.count('.') != 2:
                logging.error(f"Token com formato inválido: {token[:30]}...")
                raise InvalidToken("Formato de token inválido")
                
            token_data = decode_token(token)

            if not token_data:
                raise InvalidToken("Token inválido ou expirado")

            jti = token_data.get("jti")
            if jti and redis_client.is_token_blacklisted(jti):
                raise InvalidToken("Token revogado ou inválido")

            self.verify_token_data(token_data)

            return token_data
            
        except HTTPException:
            raise
        except Exception as e:
            import logging
            logging.error(f"Erro inesperado na autenticação: {str(e)}")
            raise InvalidToken("Erro na validação do token")

    def verify_token_data(self, token_data: dict) -> None:
        raise NotImplementedError("Este método deve ser implementado nas classes filhas")

class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data.get("refresh"):
            raise AccessTokenRequired()

class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if not token_data.get("refresh"):
            raise RefreshTokenRequired()


def get_current_user(
    token_details: dict = Depends(AccessTokenBearer()),
    db: Session = Depends(get_session),
) -> User:
    user_service = UserService()
    
    if not token_details or not token_details.get("user") or not token_details["user"].get("email"):
        raise InvalidToken("Token não contém informações válidas do usuário")
        
    user_email = token_details["user"]["email"]
    
    user = user_service.get_user_by_email(user_email, db)
    
    if not user:
        raise UserNotFound()
        
    return user

class RoleChecker:
    
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> bool:
        if not current_user.is_verified:
            raise AccountNotVerified()
            
        if current_user.role in self.allowed_roles:
            return True

        raise InsufficientPermission()
