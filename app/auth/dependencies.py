from typing import Any, List

from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db as get_session
from app.errors import AccessTokenRequired, InvalidToken, RefreshTokenRequired, UserNotFound, InsufficientPermission, AccountNotVerified
from app.models.login_record import User
from app.database.redis import RedisClient as redis_client

from .service import UserService
from .utils import decode_token

user_service = UserService()

class TokenBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    def __call__(self, request: Request) -> dict:
        credentials: HTTPAuthorizationCredentials = super().__call__(request)
        # credentials = super().__call__(request)
        
        if not credentials:
            raise InvalidToken()

        token = credentials.credentials
        token_data = decode_token(token)

        if not token_data:
            raise InvalidToken()

        if redis_client.is_token_blacklisted(token_data["jti"]):
            raise InvalidToken()

        self.verify_token_data(token_data)

        return token_data

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
