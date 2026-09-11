import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.crowd_management import classify_crowd, compute_utilisation

def test_classify_crowd():
    assert classify_crowd(0.10) == "Low"
    assert classify_crowd(0.49) == "Low"
    assert classify_crowd(0.50) == "Moderate"
    assert classify_crowd(0.74) == "Moderate"
    assert classify_crowd(0.75) == "High"
    assert classify_crowd(0.89) == "High"
    assert classify_crowd(0.90) == "Critical"
    assert classify_crowd(1.50) == "Critical"

def test_compute_utilisation():
    # 50 passengers on a 100 capacity bus
    assert compute_utilisation(50, capacity=100) == 0.50
    # 120 passengers on a 100 capacity bus
    assert compute_utilisation(120, capacity=100) == 1.20
    # Uses default capacity (100) if not provided
    assert compute_utilisation(85, route="Unknown Route") == 0.85
