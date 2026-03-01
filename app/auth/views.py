from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session as SQLAlchemySession
from app.auth import User, UserRole, get_user
from app.auth.utils import make_password
from app.database import get_session


class AuthenticationApiView:

    @staticmethod
    async def post(
        self, username: str, password: str, db: SQLAlchemySession = Depends(get_session)
    ):
        pass
