from prometheus_client import REGISTRY
from metrics import track_notification


def sample(result):
    return REGISTRY.get_sample_value("notifications_total", {"result": result}) or 0


async def test_track_notification_counts_sent_and_failed():
    @track_notification
    async def ok():
        return True

    @track_notification
    async def bad():
        return False

    sent, failed = sample("sent"), sample("failed")
    assert await ok() is True
    assert await bad() is False
    assert sample("sent") == sent + 1
    assert sample("failed") == failed + 1


async def test_metrics_endpoint_counts_requests(client):
    await client.get("/health")
    res = await client.get("/metrics")
    assert res.status_code == 200
    assert 'http_requests_total{method="GET",path="/health",status="200"}' in res.text
