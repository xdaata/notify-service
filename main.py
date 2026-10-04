from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from api.events import router as events_router
from config import settings
from logging_config import setup_logging

setup_logging()

app = FastAPI(title="Notify Service")

STATIC_DIR = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(events_router)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "telegram_configured": bool(settings.telegram_bot_token != "your_bot_token_here"),
    }
