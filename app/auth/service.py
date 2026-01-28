from typing import Optional
from sqlalchemy.orm import Session

from jwt import ExpiredSignatureError, InvalidTokenError
from app.models.login_record import User
from .schemas import UserCreateModel
from .utils import decode_jwt, generate_passwd_hash


class SessionDataSource:

    @classmethod
    def get_token(cls, token: str) -> dict:

        try:
            token_contents = decode_jwt(token)

        except (ExpiredSignatureError, KeyError):
            raise ExpiredSignatureError

        except (InvalidTokenError, ValueError):
            raise InvalidTokenError

        return token_contents


class UsuarioTokenService:

    def get_user_by_email(self, email: str, db: Session) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def user_exists(self, email: str, db: Session) -> bool:
        user = self.get_user_by_email(email, db)
        return user is not None

    def create_user(self, user_data: UserCreateModel, db: Session) -> User:
        data = user_data.dict()
        password = data.pop("password")

        new_user = User(
            **data,
            password_hash=generate_passwd_hash(password),
            role="user",
            is_verified=False
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    def update_user(self, user: User, user_data: dict, db: Session) -> User:
        for key, value in user_data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user
