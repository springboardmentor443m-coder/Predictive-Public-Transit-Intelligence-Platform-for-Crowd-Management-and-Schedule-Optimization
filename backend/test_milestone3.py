"""
test_milestone3.py
Automated validation suite for Milestone 3 endpoints.
"""

import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_test(name, path, method="GET", payload=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8") if payload else None
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
            body = json.loads(response.read().decode("utf-8"))
            print(f"PASS: {name} (Status {status})")
            return body
    except Exception as e:
        print(f"FAIL: {name} - Error: {e}")
        return None

def main():
    print("\n--- Starting Milestone 3 Validation Suite ---\n")
    
    # 1. Test live alerts
    run_test("Get Live Alerts", "/api/v1/alerts/live")
    
    # 2. Test emergency broadcast
    emergency_payload = {
        "line": "Red Line Express",
        "severity": "CRITICAL",
        "message": "Platform overcrowding detected. Hold trains at junction.",
        "operator_id": "OP-994"
    }
    run_test("Broadcast Emergency", "/api/v1/alerts/emergency", method="POST", payload=emergency_payload)
    
    # 3. Test active announcements
    run_test("Get Active Announcements", "/api/v1/alerts/announcements")
    
    # 4. Test headway manual override
    update_payload = {
        "trip_id": "LINE-A-01",
        "new_headway_minutes": 4,
        "reason": "Commuter surge compensation"
    }
    run_test("Update Headway", "/api/v1/scheduling/update-headway", method="POST", payload=update_payload)
    
    # 5. Test Network KPIs
    run_test("Get Network KPIs", "/api/v1/analytics/kpis")
    
    # 6. Test Congestion Heatmap
    run_test("Get Congestion Heatmap", "/api/v1/analytics/heatmap")
    
    print("\n--- Validation Suite Complete ---\n")

if __name__ == "__main__":
    main()