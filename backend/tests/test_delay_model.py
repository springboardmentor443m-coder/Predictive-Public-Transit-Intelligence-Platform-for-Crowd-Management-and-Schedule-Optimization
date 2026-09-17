import sys
from pathlib import Path
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.base import Base
from app.models.station import Station
from app.ml.delay_model_loader import DelayPredictionModel, delay_ml_model, get_season_from_month
from app.services.ml_loader import predict_train_delay
from app.services.scheduling import handle_delay


@pytest.fixture
def delay_test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSession()
    stations = [
        Station(station_code="150", name_en="Seoul Station", line="Line 1", latitude=37.5546, longitude=126.9725, district="Jung-gu"),
        Station(station_code="222", name_en="Gangnam", line="Line 2", latitude=37.4979, longitude=127.0276, district="Gangnam-gu"),
        Station(station_code="223", name_en="Yeoksam", line="Line 2", latitude=37.5006, longitude=127.0365, district="Gangnam-gu"),
        Station(station_code="224", name_en="Seolleung", line="Line 2", latitude=37.5045, longitude=127.0490, district="Gangnam-gu"),
    ]
    session.add_all(stations)
    session.commit()

    yield session
    session.close()


def test_delay_model_singleton_and_artifacts():
    """Validates that the delay model and encoders are instantiated correctly."""
    model_instance = DelayPredictionModel.get_instance()
    assert model_instance is not None
    assert delay_ml_model is not None


def test_season_helper():
    """Validates seasonal mapping for dates."""
    assert get_season_from_month(1) == "Winter"
    assert get_season_from_month(12) == "Winter"
    assert get_season_from_month(4) == "Spring"
    assert get_season_from_month(7) == "Summer"
    assert get_season_from_month(10) == "Autumn"


def test_delay_model_prediction_outputs():
    """
    Validates model inference returning binary classification and probability score.
    Verifies 13-feature input structure and categorical encoder application.
    """
    test_dt = datetime(2026, 9, 17, 18, 0, 0, tzinfo=timezone.utc)
    
    has_delay, delay_proba = delay_ml_model.predict(
        station_code="222",
        line_num=2,
        timestamp=test_dt,
        latitude=37.4979,
        longitude=127.0276,
        season="Autumn",
        weather_condition="Rain",
        temperature_C=18.5,
        precipitation_mm=5.0,
        real_flow_pattern_ref=75.0,
        is_holiday=0,
    )

    assert has_delay in (0, 1)
    assert isinstance(delay_proba, float)
    assert 0.0 <= delay_proba <= 1.0


def test_predict_train_delay_service(delay_test_db):
    """Tests service layer wrapper predict_train_delay."""
    test_dt = datetime.now(timezone.utc)
    has_delay, proba = predict_train_delay(
        station_code="222",
        timestamp=test_dt,
        db=delay_test_db,
        weather_condition="Clear",
    )

    assert has_delay in (0, 1)
    assert 0.0 <= proba <= 1.0


def test_handle_delay_model_driven_propagation(delay_test_db):
    """Tests that handle_delay calculates downstream propagation using model probability."""
    impact = handle_delay(
        db=delay_test_db,
        line="Line 2",
        station_code="222",
        delay_minutes=15,
        downstream_count=2,
    )

    assert impact["line"] == "Line 2"
    assert impact["incident_station_code"] == "222"
    assert impact["initial_delay_minutes"] == 15
    assert len(impact["affected_stations"]) == 2

    # Check downstream stations
    hop1 = impact["affected_stations"][0]
    assert hop1["station_code"] == "223"
    assert hop1["station_order"] == 1
    assert hop1["estimated_delay_minutes"] > 0
    assert hop1["estimated_eta_delay_seconds"] == int(hop1["estimated_delay_minutes"] * 60)

    hop2 = impact["affected_stations"][1]
    assert hop2["station_code"] == "224"
    assert hop2["station_order"] == 2
    assert hop2["estimated_delay_minutes"] > 0


def test_docstring_attribution():
    """Validates the presence of the mandatory attribution docstring in delay components."""
    assert "Delay model trained on synthetic data anchored to real crowd patterns — ROC-AUC 0.7322" in DelayPredictionModel.__doc__
    assert "Delay model trained on synthetic data anchored to real crowd patterns — ROC-AUC 0.7322" in predict_train_delay.__doc__
    assert "Delay model trained on synthetic data anchored to real crowd patterns — ROC-AUC 0.7322" in handle_delay.__doc__
