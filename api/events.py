import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from messaging.publisher import publish_event
from models import Event
from redis_client import IDEMPOTENCY_TTL_SECONDS, redis_client
from schemas import EventCreate, EventResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=202)
async def create_event(data: EventCreate, db: AsyncSession = Depends(get_db)):
    # проверка идемпотентности в redis
    cached_id = await redis_client.get(f"idempotency:{data.idempotency_key}")
    if cached_id:
        existing = await db.get(Event, uuid.UUID(cached_id))
        if existing:
            logger.info("idempotent hit id=%s", existing.id)
            return existing

    event = Event(
        event_type=data.event_type,
        payload=data.payload,
        idempotency_key=data.idempotency_key,
    )
    db.add(event)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        result = await db.execute(
            select(Event).where(Event.idempotency_key == data.idempotency_key)
        )
        existing = result.scalar_one()
        logger.info("idempotency key collision id=%s", existing.id)
        return existing

    await db.refresh(event)

    await redis_client.set(
        f"idempotency:{data.idempotency_key}", str(event.id), ex=IDEMPOTENCY_TTL_SECONDS
    )
    await publish_event(event.id)
    logger.info("event queued id=%s type=%s", event.id, event.event_type)

    return event


@router.get("", response_model=list[EventResponse])
async def list_events(
        limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Event).order_by(Event.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
