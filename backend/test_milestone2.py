import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000"

ENDPOINTS = [
    ("/api/v1/scheduling/timetable", "Step 6: Timetable"),
    ("/api/v1/scheduling/frequency", "Step 7: Frequency Adjustment"),
    ("/api/v1/scheduling/peak-optimization", "Step 8: Peak-Hour Optimization"),
    ("/api/v1/operational/telemetry", "Step 9: Operational Telemetry"),
    ("/api/v1/traffic/patterns", "Step 10: Traffic Patterns"),
    ("/api/v1/traffic/report", "Step 11: Analysis Report"),
    ("/api/v1/ai/recommendations", "Step 12: Smart AI Recommendations"),
]

def run_tests():
    print("=" * 60)
    print("RUNNING MILESTONE 2 AUTOMATED TEST SUITE")
    print("=" * 60)
    
    passed = 0
    for path, description in ENDPOINTS:
        url = f"{BASE_URL}{path}"
        try:
            req = urllib.request.urlopen(url, timeout=5)
            status = req.getcode()
            data = json.loads(req.read().decode())
            has_data = len(data) > 0 if isinstance(data, list) else ("error" not in data)
            
            if status == 200 and has_data:
                print(f"[PASS] {description:<32} (HTTP 200 OK)")
                passed += 1
            else:
                print(f"[FAIL] {description:<32} (Empty or error payload)")
        except Exception as err:
            print(f"[ERROR] {description:<31} ({err})")

    print("-" * 60)
    print(f"RESULTS: {passed}/{len(ENDPOINTS)} tests passed.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()