from enum import Enum
import uuid
from datetime import datetime, timezone
from app.database import Base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column


class StatusEnum(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        unique=True,
        index=True,
        nullable=False,
        default=uuid.uuid4,
    )
    full_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password: Mapped[str] = mapped_column(String)
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum))
    created_date: Mapped[datetime | None] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    updated_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
