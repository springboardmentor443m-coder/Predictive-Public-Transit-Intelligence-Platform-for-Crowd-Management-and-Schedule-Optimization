import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.schedule_optimizer import generate_recommendation

def test_generate_recommendation_critical():
    rec = generate_recommendation("Route 1", 8, passenger_count=95, capacity=100)
    assert rec["crowd_level"] == "Critical"
    assert "Add an extra vehicle" in rec["action"]
    assert rec["priority"] == 1

def test_generate_recommendation_low():
    rec = generate_recommendation("Route 1", 14, passenger_count=15, capacity=100)
    assert rec["crowd_level"] == "Low"
    assert rec["priority"] == 4
    # Below very low threshold (20%)
    assert "consolidating" in rec["reason"].lower() or "reducing" in rec["reason"].lower()
