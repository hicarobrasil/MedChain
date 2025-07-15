from pydantic import BaseModel, EmailStr, Field, constr
from typing import Optional, Union
from uuid import UUID
from datetime import datetime

class DoctorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    crm: str = Field(..., min_length=4, max_length=20)
    specialty: Union[int, str]
    email: EmailStr
    phone: str = Field(..., min_length=8, max_length=20)
    status: Union[int, str]
    hospital_affiliation: Optional[str] = None
    office_address: Optional[str] = None

class DoctorCreate(DoctorBase):
    pass

class DoctorUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    crm: Optional[str] = Field(default=None, min_length=4, max_length=20)
    specialty: Optional[Union[int, str]] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, min_length=8, max_length=20)
    status: Optional[Union[int, str]] = None
    hospital_affiliation: Optional[str] = None
    office_address: Optional[str] = None

class DoctorOut(BaseModel):
    uid: UUID
    name: str
    crm: str
    specialty: str
    email: EmailStr
    phone: str
    status: str
    hospital_affiliation: Optional[str] = None
    office_address: Optional[str] = None
    date_created: datetime
    date_updated: datetime

    class Config:
        orm_mode = True
