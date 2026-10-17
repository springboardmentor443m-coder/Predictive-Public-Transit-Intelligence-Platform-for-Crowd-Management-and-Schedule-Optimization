import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone
from app.models.alert import OperationalAlertModel, AlertType, AlertSeverity, AlertStatus
from app.services.alert_service import OperationalAlertService
from app.models.trip_update import TripUpdateModel
from app.models.service_alert import ServiceAlertModel
from app.schemas.live_data import DataState


@pytest.fixture(autouse=True)
def mock_mta_network_calls():
    with patch("app.services.live_data.ingestion.mta_provider.fetch_all_normalized_entities", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = ([], [], [])
        yield mock_fetch


def test_alert_sync_and_deduplication(db_session):
    now_utc = datetime.now(timezone.utc)
    
    # Add dummy live delay to test live delay alert generation
    delay = TripUpdateModel(
        trip_id="TEST_TRIP_001",
        route_id="A",
        stop_id="A27",
        delay_seconds=240.0,
        timestamp=now_utc,
        data_state=DataState.LIVE
    )
    db_session.add(delay)

    # Add dummy MTA service alert
    service_alt = ServiceAlertModel(
        alert_id="MTA_BULLETIN_999",
        header_text="Signal Maintenance on 8th Ave Line",
        description_text="Expect minor delays on A, C, E trains during signal maintenance work.",
        affected_routes=["A", "C", "E"],
        active=True,
        timestamp=now_utc,
        data_state=DataState.LIVE
    )
    db_session.add(service_alt)
    db_session.commit()

    # Sync alerts
    res = OperationalAlertService.sync_alerts(db_session)
    assert "active_count" in res
    assert res["active_count"] > 0

    # Test deduplication: running sync again shouldn't create duplicate entries
    count_first = db_session.query(OperationalAlertModel).count()
    res2 = OperationalAlertService.sync_alerts(db_session)
    count_second = db_session.query(OperationalAlertModel).count()
    assert count_first == count_second

    # Check alert types present
    alert_types = {a.alert_type for a in db_session.query(OperationalAlertModel).all()}
    assert AlertType.LIVE_DELAY in alert_types or AlertType.OVERCROWDING in alert_types


def test_get_active_alerts_api(client):
    response = client.get("/api/v1/alerts/active")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_alert_summary_api(client):
    response = client.get("/api/v1/alerts/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_active" in data
    assert "critical_count" in data
    assert "live_delays_count" in data


def test_acknowledge_alert_api(client, operator_user, operator_headers, db_session):
    now_utc = datetime.now(timezone.utc)
    OperationalAlertService.sync_alerts(db_session)
    alert = db_session.query(OperationalAlertModel).filter(OperationalAlertModel.status == AlertStatus.ACTIVE).first()
    
    if not alert:
        alert = OperationalAlertModel(
            alert_key="TEST_ALERT_101",
            alert_type=AlertType.OVERCROWDING,
            severity=AlertSeverity.HIGH,
            status=AlertStatus.ACTIVE,
            title="Test Overcrowding Alert",
            description="Test alert for acknowledgement unit test.",
            timestamp=now_utc,
            updated_at=now_utc,
            data_state=DataState.PREDICTED
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

    response = client.post(
        f"/api/v1/alerts/{alert.id}/acknowledge",
        json={"note": "Reviewed by unit test operator."},
        headers=operator_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACKNOWLEDGED"
    assert data["acknowledged_by"] is not None


def test_alert_lifecycle_resolution(db_session):
    now_utc = datetime.now(timezone.utc)
    orphan_alert = OperationalAlertModel(
        alert_key="TEMPORARY_STALE_EVENT_999",
        alert_type=AlertType.LIVE_DELAY,
        severity=AlertSeverity.WARNING,
        status=AlertStatus.ACTIVE,
        title="Temporary Stale Delay Alert",
        description="Event that will clear.",
        timestamp=now_utc,
        updated_at=now_utc,
        data_state=DataState.LIVE
    )
    db_session.add(orphan_alert)
    db_session.commit()

    OperationalAlertService.sync_alerts(db_session)
    fetched = db_session.query(OperationalAlertModel).filter(OperationalAlertModel.alert_key == "TEMPORARY_STALE_EVENT_999").first()
    assert fetched is not None
    assert fetched.status == AlertStatus.RESOLVED
