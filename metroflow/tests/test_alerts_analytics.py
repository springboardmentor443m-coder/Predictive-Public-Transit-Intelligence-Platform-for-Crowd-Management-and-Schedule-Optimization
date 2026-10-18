from tests.conftest import BUSY, DATE


def test_overcrowding_alerts_respect_threshold(client, admin):
    r = client.get("/alerts/overcrowding", headers=admin, params={"on_date": DATE, "hour": 18}).json()
    assert all(a["congestion_pct"] >= 85 for a in r["alerts"])


def test_forecasted_alerts_endpoint(client, admin):
    r = client.get(f"/alerts/forecasted/{BUSY}", headers=admin, params={"on_date": DATE})
    assert r.status_code == 200 and isinstance(r.json()["alerts"], list)


def test_delay_alerts_only_report_significant_delays(client, admin):
    # scan a few days so at least some alerts exist, and every one must respect the threshold
    found = []
    for d in ("2023-12-27", "2023-12-28", "2023-12-29"):
        for h in range(24):
            found += client.get("/alerts/delays", headers=admin, params={"on_date": d, "hour": h}).json()["alerts"]
    assert all(a["delay_minutes"] >= 7 for a in found)


def test_emergency_announcement_admin_only_and_validated(client, admin, operator):
    body = {"station": "Ximen", "message": "Track obstruction - expect delays"}
    ok = client.post("/alerts/emergency", headers=admin, json=body)
    assert ok.status_code == 200 and ok.json()["type"] == "EMERGENCY"
    assert client.post("/alerts/emergency", headers=operator, json=body).status_code == 403
    assert client.post("/alerts/emergency", headers=admin, json={**body, "station": "Atlantis"}).status_code == 404
    assert client.post("/alerts/emergency", headers=admin, json={**body, "message": "x"}).status_code == 422


def test_live_feed_combines_alert_types(client, admin):
    f = client.get("/alerts/live-feed", headers=admin, params={"on_date": DATE, "hour": 18}).json()
    assert {"overcrowding_alerts", "delay_alerts", "anomaly_alerts"} <= set(f)


def test_traffic_report(client, admin):
    r = client.get("/analytics/traffic", headers=admin, params={"days": 7}).json()
    assert r["total_entries"] > 0 and len(r["busiest_stations"]) == 5
    entries = [s["Entries"] for s in r["busiest_stations"]]
    assert entries == sorted(entries, reverse=True) and r["busiest_stations"][0]["Station"] == BUSY


def test_station_performance_report(client, admin):
    r = client.get(f"/analytics/station/{BUSY}", headers=admin).json()
    assert {"crowd_analytics", "delay_profile", "ai_insights"} <= set(r)


def test_operational_summary(client, admin):
    r = client.get("/analytics/operational-summary", headers=admin, params={"on_date": DATE, "hour": 18}).json()
    assert r["critical_station_count"] + r["healthy_station_count"] == 30


def test_heatmap_report_ranks_worst_points(client, admin):
    r = client.get("/analytics/heatmap-report", headers=admin, params={"on_date": DATE}).json()
    pcts = [w["peak_congestion_pct"] for w in r["worst_congestion_points"]]
    assert len(pcts) == 5 and pcts == sorted(pcts, reverse=True)


def test_ai_insights_bundle(client, admin):
    r = client.get(f"/analytics/ai-insights/{BUSY}", headers=admin, params={"on_date": DATE}).json()
    assert len(r["forecast"]) == 24 and r["model_metadata"]["demand"]["selected_model"]


def test_admin_only_analytics_blocked_for_operator(client, operator):
    assert client.get("/analytics/traffic", headers=operator).status_code == 403
    assert client.get("/alerts/live-feed", headers=operator, params={"on_date": DATE, "hour": 8}).status_code == 403
