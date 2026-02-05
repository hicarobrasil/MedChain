from datetime import date
from pydantic import BaseModel, EmailStr


class PatientRequest(BaseModel):
    name: str
    dateofbirth: date
    gender: int 
    email: EmailStr
    phone: str
    status: int
    address_street: str
    address_number:str
    address_complement:str
    address_neighborhood:str
    address_city:str
    address_state:str
    
    