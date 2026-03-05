from .urls import router as doctor_router
from .schemas import DoctorIn, DoctorUpdate, DoctorOut

__all__ = ["doctor_router", "DoctorIn", "DoctorUpdate", "DoctorOut"]
