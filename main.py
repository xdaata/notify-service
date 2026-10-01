from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from api.events import router as events_router
from config import settings
from logging_config import setup_logging

setup_logging()

app = FastAPI(title="Notify Service")

app.include_router(events_router)

INDEX_PATH = Path(__file__).parent / "static" / "index.html"


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(INDEX_PATH)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "telegram_configured": bool(settings.telegram_bot_token != "your_bot_token_here"),
    }
