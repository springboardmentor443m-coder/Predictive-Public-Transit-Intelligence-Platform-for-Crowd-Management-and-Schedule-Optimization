import sys
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sklearn.preprocessing import LabelEncoder
from src.feature_engineering import build_inference_row
from src.config import FEATURE_COLUMNS

def test_build_inference_row():
    # Setup mock encoder
    encoder = LabelEncoder()
    encoder.fit(["Route A", "Route B"])
    
    # Run build
    row = build_inference_row(
        route="Route A",
        hour=8,          # Peak hour
        day_of_week=5,   # Weekend
        temperature=20.0,
        is_raining=1,
        nearby_event=0,
        prev_passenger_count=45,
        route_avg_demand=50,
        route_encoder=encoder
    )
    
    # Assert shape is (1, number_of_features)
    assert row.shape == (1, len(FEATURE_COLUMNS))
    
    # Extract values for checks (assuming fixed order in config)
    # ['route_encoded', 'hour', 'day_of_week', 'is_weekend', 'is_peak_hour', 'temperature', 'is_raining', 'nearby_event', 'prev_passenger_count', 'route_avg_demand']
    
    assert row[0, 1] == 8       # hour
    assert row[0, 2] == 5       # day_of_week
    assert row[0, 3] == 1       # is_weekend (5 is Saturday)
    assert row[0, 4] == 1       # is_peak_hour (8 is AM peak)
    assert row[0, 5] == 20.0    # temperature
    assert row[0, 6] == 1       # is_raining
