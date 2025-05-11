import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, VARCHAR as PG_VARCHAR

from app.database import Base

class User(Base):
    __tablename__ = "users"

    uid = Column(PG_UUID(as_uuid=True), nullable=False, primary_key=True, default=uuid.uuid4)
    username = Column(String(50), index=True, nullable=False)
    email = Column(String(100), index=True, nullable=False)
    password_hash = Column(PG_VARCHAR(150), nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    role = Column(PG_VARCHAR(50), nullable=False, server_default="user")
    is_verified = Column(Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            "uid": self.uid,
            "email": self.email,
            "date_created": self.date_created.isoformat(),
            "date_updated": self.date_updated.isoformat(),
            "role": self.role,
        }
