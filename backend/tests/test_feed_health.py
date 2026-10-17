from datetime import datetime, timedelta, timezone
from app.services.live_data.mta_subway import MTASubwayLiveDataProvider
from app.models.feed_status import HealthStatus


def test_feed_health_staleness_detection():
    provider = MTASubwayLiveDataProvider()
    provider.last_status = HealthStatus.LIVE
    provider.last_sync_time = datetime.now(timezone.utc) - timedelta(seconds=120)

    status = provider.get_status()
    assert status.is_connected is True
    assert provider.last_status == HealthStatus.STALE


def test_feed_health_offline_detection():
    provider = MTASubwayLiveDataProvider()
    provider.last_status = HealthStatus.ERROR
    provider.last_error = "Connection Timeout 408"

    status = provider.get_status()
    assert status.is_connected is False
    assert "ERROR" in status.status_message
