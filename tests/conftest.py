import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from db import async_session
from main import app
from models import Event

# все тестовые события помечаем этим префиксом в idempotency_key,
# чтобы точно знать, что можно безопасно удалить после теста
TEST_PREFIX = "pytest-"


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_events():
    yield
    async with async_session() as session:
        await session.execute(
            delete(Event).where(Event.idempotency_key.like(f"{TEST_PREFIX}%"))
        )
        await session.commit()
