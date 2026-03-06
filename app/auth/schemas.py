import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr, Field

class UserCreateModel(BaseModel):
    username: str = Field(max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)

    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "johndoe@example.com",
                "password": "securepass123",
            }
        }

class UserLoginModel(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class EmailModel(BaseModel):
    addresses: List[str]

class PasswordResetRequestModel(BaseModel):
    email: EmailStr

class PasswordResetConfirmModel(BaseModel):
    new_password: str = Field(min_length=6)
    confirm_new_password: str = Field(min_length=6)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class DoctorRegisterModel(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=6)
    CRM: str
    specialty: str
