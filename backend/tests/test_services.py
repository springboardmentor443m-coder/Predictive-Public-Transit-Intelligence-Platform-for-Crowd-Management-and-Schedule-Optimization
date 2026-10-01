from app.services.alert_service import generate_alerts
from app.services.announcement_service import create_announcement
from app.services.analytics_service import generate_analytics
from app.services.realtime_service import get_realtime_update


def test_alerts_detect_overcrowding():
    result = generate_alerts(predicted_ridership=600)
    assert result["alert_count"] >= 1
    assert any(alert["type"] == "overcrowding" for alert in result["alerts"])


def test_alerts_detect_congestion():
    result = generate_alerts(traffic_level="high")
    assert any(alert["type"] == "congestion" for alert in result["alerts"])


def test_alerts_detect_major_delay():
    result = generate_alerts(delay_minutes=20)
    assert any(alert["type"] == "delay" for alert in result["alerts"])


def test_alerts_normal_state():
    result = generate_alerts()
    assert result["alert_count"] == 1
    assert result["alerts"][0]["type"] == "system"


def test_create_announcement():
    result = create_announcement(
        title="Emergency",
        message="Please follow station instructions.",
        severity="high",
        station="Central Station",
    )
    announcement = result["announcement"]
    assert announcement["title"] == "Emergency"
    assert announcement["station"] == "Central Station"
    assert announcement["severity"] == "high"
    assert announcement["status"] == "active"


def test_generate_analytics():
    result = generate_analytics(
        total_passengers=10000,
        active_alerts=3,
        delayed_trains=1,
        average_delay=8,
        peak_crowd_level="high",
    )
    analytics = result["analytics"]
    assert analytics["total_passengers"] == 10000
    assert analytics["active_alerts"] == 3
    assert analytics["delayed_trains"] == 1
    assert analytics["average_delay_minutes"] == 8
    assert analytics["peak_crowd_level"] == "high"
    assert result["status"] == "available"


def test_realtime_update():
    result = get_realtime_update(
        station="Central Station",
        crowd_level="high",
        train_status="delayed",
        delay_minutes=8,
    )
    assert result["station"] == "Central Station"
    assert result["crowd_level"] == "high"
    assert result["train_status"] == "delayed"
    assert result["delay_minutes"] == 8
    assert result["status"] == "live"
    assert "last_updated" in result


def test_realtime_default_values():
    result = get_realtime_update(station="Central Station")
    assert result["crowd_level"] == "normal"
    assert result["train_status"] == "on_time"
    assert result["delay_minutes"] == 0
    assert result["status"] == "live"
