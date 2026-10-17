import pytest
from app.services.ml_service import MLDataService
from fastapi import HTTPException
from unittest.mock import MagicMock

def test_historical_csv_predictions_not_live():
    service = MLDataService.get_instance()
    summary = service.get_summary()
    assert summary["data_state"] in ["HISTORICAL CSV", "LIVE TELEMETRY"]

def test_db_failure_returns_503():
    service = MLDataService.get_instance()
    mock_db = MagicMock()
    mock_db.query.side_effect = Exception("DB Connection Error")
    
    with pytest.raises(HTTPException) as excinfo:
        service.get_delay_impact(db=mock_db)
    
    assert excinfo.value.status_code == 503
    assert "Database unavailable" in excinfo.value.detail

from datetime import datetime, timezone, timedelta

def test_valid_zero_delay():
    service = MLDataService.get_instance()
    mock_db = MagicMock()
    
    # Mocking query().scalar() to return count=100 and latest=now
    def mock_scalar():
        return datetime.now(timezone.utc).replace(tzinfo=None)
        
    # We need to distinguish between the two scalar() calls.
    # We can just return values in order using side_effect for scalar
    mock_db.query.return_value.scalar.side_effect = [100, datetime.now(timezone.utc).replace(tzinfo=None)]
    
    # Mocking query().group_by().all() to return empty list
    mock_db.query.return_value.group_by.return_value.all.return_value = []
    
    result = service.get_delay_impact(db=mock_db)
    # Check first route
    assert result[0]["delay_seconds"] == 0.0
    assert result[0]["severity_tier"] == "LOW_DELAY"
    assert result[0]["data_state"] == "LIVE (NO DELAY)"

def test_delay_impact_unavailable():
    service = MLDataService.get_instance()
    mock_db = MagicMock()
    
    mock_db.query.return_value.scalar.side_effect = [0]
    mock_db.query.return_value.group_by.return_value.all.return_value = []
    
    result = service.get_delay_impact(db=mock_db)
    assert result[0]["data_state"] == "UNAVAILABLE"

def test_delay_impact_stale():
    service = MLDataService.get_instance()
    mock_db = MagicMock()
    
    # 10 minutes ago
    stale_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=10)
    mock_db.query.return_value.scalar.side_effect = [100, stale_time]
    mock_db.query.return_value.group_by.return_value.all.return_value = []
    
    result = service.get_delay_impact(db=mock_db)
    assert result[0]["data_state"] == "STALE"

def test_unverified_metrics():
    service = MLDataService.get_instance()
    result = service.get_network_summary()
    assert result["delay_model_accuracy"] is None
    assert result["network_model_accuracy"] is None
    assert result["data_state"] in ["UNAVAILABLE", "LIVE (GRAPH TOPOLOGY + RANDOM FOREST PREDICTIONS)"]

def test_missing_station_thresholds():
    service = MLDataService.get_instance()
    # Temporarily clear thresholds
    old_thresholds = service.df_thresholds
    service.df_thresholds = None
    try:
        stations = service.get_stations_latest()
        # They should all fallback to UNAVAILABLE
        assert all(st["crowd_risk"] == "UNAVAILABLE" for st in stations)
    finally:
        service.df_thresholds = old_thresholds
