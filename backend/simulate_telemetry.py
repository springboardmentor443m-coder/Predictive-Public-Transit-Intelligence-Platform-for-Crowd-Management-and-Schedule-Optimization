import argparse
import json
import os
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen


API_ROOT = os.getenv("METROFLOW_API_ROOT", "http://127.0.0.1:8000")
EMAIL = os.getenv("METROFLOW_OPERATOR_EMAIL", "operator@metroflow.com")
PASSWORD = os.getenv("METROFLOW_OPERATOR_PASSWORD", "operator123")


def request_json(method: str, path: str, payload: dict | None = None, token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        f"{API_ROOT.rstrip('/')}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers,
        method=method,
    )
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read())


def build_payload(summary: dict, cycle: int) -> dict:
    trains = []
    for index, train in enumerate(summary.get("trains", [])):
        is_delayed = (cycle + index) % 5 == 0
        trains.append(
            {
                **train,
                "status": "Delayed" if is_delayed else "On time",
                "next_arrival": f"{3 + ((cycle + index) % 6)} min",
            }
        )

    alerts = list(summary.get("alerts", []))
    if cycle % 3 == 0 and trains:
        alerts.insert(
            0,
            {
                "type": "warning",
                "title": "Telemetry simulator detected service variance",
                "detail": f"{trains[0]['service']} · {trains[0]['line']} · Arrival estimate updated",
                "time": datetime.now(timezone.utc).strftime("%H:%M UTC"),
                "action": "Review service",
            },
        )

    schedule = dict(summary.get("schedule", {}))
    schedule["recommended_headway_minutes"] = 3 if cycle % 4 == 0 else 5
    schedule["confidence"] = max(80, 95 - (cycle % 10))

    return {
        "active_services": summary.get("active_services", len(trains) * 10),
        "trains": trains,
        "alerts": alerts,
        "schedule": schedule,
    }


def run(once: bool, interval: int) -> None:
    login = request_json(
        "POST",
        "/login",
        {"email": EMAIL, "password": PASSWORD, "role": "Operator"},
    )
    token = login["access_token"]
    cycle = 0

    while True:
        summary = request_json("GET", "/api/v1/operations/summary", token=token)
        payload = build_payload(summary, cycle)
        request_json("POST", "/api/v1/operations/telemetry", payload, token)
        print(f"Telemetry snapshot {cycle} stored at {API_ROOT}")
        cycle += 1
        if once:
            return
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send development telemetry to MetroFlow.")
    parser.add_argument("--once", action="store_true", help="Send one snapshot and exit")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between snapshots")
    args = parser.parse_args()
    run(once=args.once, interval=args.interval)
