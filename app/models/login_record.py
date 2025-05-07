from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime

from app.database import Base

class LoginRecord(Base):
    
    __tablename__ = "login_records"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True, nullable=False)
    email = Column(String(100), index=True, nullable=False)
    password = Column(String(255), nullable=False) 
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Converte o registro de login em um dicionário."""
        return {
            "id": self.id,
            "email": self.email,
            "date_created": self.date_created.isoformat(),
            "date_updated": self.date_updated.isoformat(),
        }

