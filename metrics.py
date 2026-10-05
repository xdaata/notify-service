import functools
import time
from prometheus_client import Counter, Histogram

# запросы по методу, маршруту и коду ответа
http_requests = Counter(
    "http_requests_total", "http requests handled by the api", ["method", "path", "status"]
)

# итог обработки каждого события и сколько это заняло
notifications = Counter("notifications_total", "events handled by the worker", ["result"])
handle_seconds = Histogram(
    "notification_handle_seconds", "time to handle one event, retries included"
)


def track_notification(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        ok = await func(*args, **kwargs)
        handle_seconds.observe(time.perf_counter() - start)
        notifications.labels(result="sent" if ok else "failed").inc()
        return ok

    return wrapper
