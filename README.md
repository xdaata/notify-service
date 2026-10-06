# Notify Service

Сервис уведомлений на FastAPI: принимает события по HTTP и отправляет их в Telegram через очередь сообщений RabbitMQ, с идемпотентностью и повторными попытками отправки.

## Стек

Python 3.14, FastAPI, PostgreSQL, Async SQLAlchemy, Alembic, Redis, RabbitMQ, Docker, Pytest, prometheus-client.

## Запуск

Для отправки сообщений нужен свой Telegram-бот:

1. Написать [@BotFather](https://t.me/BotFather), отправить `/newbot` и получить токен.
2. Написать своему боту любое сообщение, открыть `https://api.telegram.org/bot<токен>/getUpdates` и найти `"chat":{"id":...}` — это id чата.
3. Скопировать `.env.example` в `.env` и заполнить `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`.

Запустить контейнеры:

```
docker compose up --build -d
```

После запуска веб-интерфейс доступен на `http://localhost:8000`.

## Остановка

Остановить контейнеры:

```
docker compose down
```

Остановить и очистить данные баз:

```
docker compose down -v
```