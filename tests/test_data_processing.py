import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.data_processing import get_data_summary

def test_get_data_summary():
    df = pd.DataFrame({
        "route": ["Route A", "Route A", "Route B"],
        "passenger_count": [10, 50, 100],
        "utilisation": [0.1, 0.5, 1.0],
    })
    
    summary = get_data_summary(df)
    
    assert summary["total_routes"] == 2
    assert summary["total_records"] == 3
    assert summary["peak_demand"] == 100
    assert summary["avg_utilisation"] == 53.3

import pytest
