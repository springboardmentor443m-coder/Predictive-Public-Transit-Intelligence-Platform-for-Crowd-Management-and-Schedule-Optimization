"""
Verification script for updated seed credentials and new implemented endpoints:
- POST /api/v1/schedule/override
- POST /api/v1/alerts/broadcast
File: eval/verify_security_updates.py
"""

import os
import sys

# Ensure backend directory is in path and configure environment
backend_dir = os.path.abspath("backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["DATABASE_URL"] = "sqlite:///F:/MetroFlow-AI-Platform-for-Metro-Crowd-Management-Scheduling-main/MetroFlow-AI-Platform-for-Metro-Crowd-Management-Scheduling-main/backend/metroflow.db"
os.environ["MODEL_PATH"] = "crowd_prediction_rf_compressed.pkl"

from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)

def run_tests():
    print("=" * 80)
    print("VERIFYING SECURITY UPDATES & NEW IMPLEMENTED ENDPOINTS")
    print("=" * 80)
    
    # 1. Test Login with Updated Environment Credentials
    print("\n[1] Testing Authentication with Environment-Derived Credentials:")
    # Admin login
    res_admin = client.post("/api/v1/auth/login", json={"username": "admin", "password": "MetroFlow@Admin2026!SecureKey#99"})
    print(f"  Admin Login (New Env Password): HTTP {res_admin.status_code}")
    assert res_admin.status_code == 200, f"Expected 200, got {res_admin.status_code}: {res_admin.text}"
    admin_token = res_admin.json()["access_token"]
    
    # Operator login
    res_op = client.post("/api/v1/auth/login", json={"username": "operator", "password": "MetroFlow@Operator2026!SecureKey#88"})
    print(f"  Operator Login (New Env Password): HTTP {res_op.status_code}")
    assert res_op.status_code == 200, f"Expected 200, got {res_op.status_code}: {res_op.text}"
    operator_token = res_op.json()["access_token"]
    
    # Verify legacy hardcoded passwords are REJECTED
    legacy_trials = [
        ("admin", "adminpassword"),
        ("admin123", "admin123"),
        ("operator", "operatorpassword"),
        ("operator123", "operator123"),
        ("station_manager", "adminpassword"),
    ]
    print("\n[2] Verifying Legacy Insecure Default Credentials are DEAD (Purged):")
    for u, p in legacy_trials:
        res_leg = client.post("/api/v1/auth/login", json={"username": u, "password": p})
        status_pass = res_leg.status_code == 401
        print(f"  Legacy trial '{u}': HTTP {res_leg.status_code} -> {'[REJECTED/SECURE]' if status_pass else '[VULNERABLE]'}")
        assert status_pass, f"Legacy credential {u} was not rejected!"
        
    # Ensure a viewer user exists in the DB for RBAC testing
    from app.db.session import SessionLocal
    from app.models.user import User
    from app.core.security import get_password_hash
    from sqlalchemy import select

    with SessionLocal() as db:
        if not db.execute(select(User).where(User.username == "test_viewer")).scalars().first():
            db.add(User(username="test_viewer", hashed_password=get_password_hash("viewerpass"), role="viewer"))
            db.commit()

    # Generate Viewer Token for RBAC tests (subject must be string username)
    viewer_token = create_access_token(subject="test_viewer", role="viewer")
    
    # 3. Test POST /api/v1/schedule/override
    print("\n[3] Testing POST /api/v1/schedule/override (Real Implementation & RBAC):")
    override_payload = {
        "line": "Line 2",
        "headway_minutes": 2.5,
        "reason": "Emergency morning crowd mitigation at Gangnam",
        "station_code": "222"
    }
    
    # No token
    res = client.post("/api/v1/schedule/override", json=override_payload)
    print(f"  No Token:          HTTP {res.status_code} (Expected 401)")
    assert res.status_code == 401
    
    # Viewer token
    res = client.post("/api/v1/schedule/override", json=override_payload, headers={"Authorization": f"Bearer {viewer_token}"})
    print(f"  Viewer Role:       HTTP {res.status_code} (Expected 403)")
    assert res.status_code == 403
    
    # Operator token
    res = client.post("/api/v1/schedule/override", json=override_payload, headers={"Authorization": f"Bearer {operator_token}"})
    print(f"  Operator Role:     HTTP {res.status_code} (Expected 200)")
    assert res.status_code == 200
    print(f"    Payload Response: {res.json()}")
    
    # Admin token
    res = client.post("/api/v1/schedule/override", json=override_payload, headers={"Authorization": f"Bearer {admin_token}"})
    print(f"  Admin Role:        HTTP {res.status_code} (Expected 200)")
    assert res.status_code == 200
    
    # 4. Test POST /api/v1/alerts/broadcast
    print("\n[4] Testing POST /api/v1/alerts/broadcast (Real Implementation & RBAC):")
    broadcast_payload = {
        "message": "Heavy platform congestion at Sindorim. Extra Line 2 trains dispatched.",
        "severity": "critical",
        "station_code": "1004",
        "alert_type": "emergency"
    }
    
    # No token
    res = client.post("/api/v1/alerts/broadcast", json=broadcast_payload)
    print(f"  No Token:          HTTP {res.status_code} (Expected 401)")
    assert res.status_code == 401
    
    # Viewer token
    res = client.post("/api/v1/alerts/broadcast", json=broadcast_payload, headers={"Authorization": f"Bearer {viewer_token}"})
    print(f"  Viewer Role:       HTTP {res.status_code} (Expected 403)")
    assert res.status_code == 403
    
    # Operator token
    res = client.post("/api/v1/alerts/broadcast", json=broadcast_payload, headers={"Authorization": f"Bearer {operator_token}"})
    print(f"  Operator Role:     HTTP {res.status_code} (Expected 201)")
    assert res.status_code == 201
    created_alert = res.json()
    print(f"    Created Alert ID {created_alert['id']}: {created_alert['message']}")
    
    # Admin token
    res = client.post("/api/v1/alerts/broadcast", json={"message": "Network-wide delay advisory.", "severity": "high"}, headers={"Authorization": f"Bearer {admin_token}"})
    print(f"  Admin Role:        HTTP {res.status_code} (Expected 201)")
    assert res.status_code == 201
    
    print("\n" + "=" * 80)
    print("ALL SECURITY & IMPLEMENTATION CHECKS PASSED PERFECTLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
