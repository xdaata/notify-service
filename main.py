from fastapi import FastAPI

from api.events import router as events_router
from config import settings

app = FastAPI(title="Notify Service")

app.include_router(events_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "telegram_configured": bool(settings.telegram_bot_token != "your_bot_token_here"),
    }
