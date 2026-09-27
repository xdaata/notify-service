import uuid
from datetime import datetime

from pydantic import BaseModel

from models import EventStatus


class EventCreate(BaseModel):
    event_type: str
    payload: dict
    idempotency_key: str


class EventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    status: EventStatus
    created_at: datetime
    error_message: str | None = None

    class Config:
        from_attributes = True  # можно строить прямо из orm-объекта