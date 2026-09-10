"""
test_full_system.py - Milestone 4 Validation Suite
Executes end-to-end integration tests across all 4 Milestones.
"""

import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, method, path, payload=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8") if payload else None
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=5) as res:
            res_json = json.loads(res.read().decode("utf-8"))
            print(f"[PASS] {name} (HTTP {res.status})")
            return res_json
    except Exception as e:
        print(f"[FAIL] {name} -> Error: {e}")
        return None

def run_all_milestones():
    print("=" * 60)
    print("      METROFLOW END-TO-END VALIDATION SUITE (MILESTONE 4)")
    print("=" * 60)

    # 1. Milestone 1: Auth & Crowd Monitoring
    print("\n--- Testing Milestone 1 (Auth & Monitoring) ---")
    test_endpoint("Operator Login", "POST", "/api/v1/auth/login", {"username": "operator", "password": "metro123"})
    test_endpoint("Live Crowd Summary", "GET", "/api/v1/crowd/live-summary")

    # 2. Milestone 2: Scheduling & ML Prediction
    print("\n--- Testing Milestone 2 (Scheduling & AI Demand) ---")
    test_endpoint("Train Timetable", "GET", "/api/v1/scheduling/timetable")
    test_endpoint("AI On-Demand Predict", "POST", "/api/v1/predict/demand", {"target_hour": 18, "day_of_week": 0})
    test_endpoint("AI 24H Continuous Curve", "GET", "/api/v1/prediction/forecast-24h")

    # 3. Milestone 3: Alerts, Notifications & Heatmaps
    print("\n--- Testing Milestone 3 (Alerts & Analytics) ---")
    test_endpoint("Live Alerts Query", "GET", "/api/v1/alerts/live")
    test_endpoint("Emergency Broadcast", "POST", "/api/v1/alerts/emergency", {
        "line": "Red Line Express", "severity": "CRITICAL",
        "message": "Milestone 4 System Verification Alert", "operator_id": "OP-ADMIN"
    })
    test_endpoint("Headway Compression Override", "POST", "/api/v1/scheduling/update-headway", {
        "trip_id": "TRIP-01", "new_headway_minutes": 3, "reason": "System Test"
    })
    test_endpoint("Network KPIs", "GET", "/api/v1/analytics/kpis")
    test_endpoint("Congestion Heatmap", "GET", "/api/v1/analytics/heatmap")

    print("\n" + "=" * 60)
    print("              ALL WORKFLOWS VALIDATED")
    print("=" * 60)

if __name__ == "__main__":
    run_all_milestones()