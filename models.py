import enum
import uuid
from datetime import datetime
from sqlalchemy import JSON, DateTime, Enum, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EventStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # то, что прислал клиент в POST /events - тип события и произвольные данные
    event_type: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON)

    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus), default=EventStatus.QUEUED
    )

    # идемпотентность на уровне бд - второй такой же ключ вставить нельзя.
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True)

    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
