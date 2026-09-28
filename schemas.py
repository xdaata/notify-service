import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from models import EventStatus


class EventCreate(BaseModel):
    event_type: str
    payload: dict
    idempotency_key: str


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # можно строить прямо из orm-объекта

    id: uuid.UUID
    event_type: str
    status: EventStatus
    created_at: datetime
    error_message: str | None = None
