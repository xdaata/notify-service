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

    class Config:
        from_attributes = True  # можно строить схему прямо из orm-объекта
