from fastapi import FastAPI
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    rabbitmq_url: str
    telegram_bot_token: str
    telegram_chat_id: str

    class Config:
        env_file = ".env"


settings = Settings()

app = FastAPI(title="Notify Service")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "telegram_configured": bool(settings.telegram_bot_token != "your_bot_token_here"),
    }
