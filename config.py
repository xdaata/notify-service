from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    redis_url: str
    rabbitmq_url: str
    telegram_bot_token: str
    telegram_chat_id: str


settings = Settings()
