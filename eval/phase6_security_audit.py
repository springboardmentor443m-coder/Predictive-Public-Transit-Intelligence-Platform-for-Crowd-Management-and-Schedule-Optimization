import os
import sys
import time
from datetime import datetime, timedelta, timezone
from jose import jwt

# Configure backend environment
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(repo_root, "backend")
db_file = os.path.join(backend_dir, "metroflow.db").replace('\\', '/')
model_file = os.path.abspath(os.path.join(repo_root, "..", "crowd_prediction_rf_compressed.pkl")).replace('\\', '/')

os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
os.environ["MODEL_PATH"] = model_file

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.database import SessionLocal
from app.models.user import User
from app.models.alert import Alert
from sqlalchemy import select

print("=" * 80)
print("METROFLOW AUDIT - PHASE 6: Security and Correctness Audit")
print("=" * 80)

client = TestClient(app)
db = SessionLocal()

# 1. Check Hardcoded Default Credentials
print("\n[1] AUDIT: Hardcoded Default Credentials Check")
print("-" * 80)
users_in_db = db.execute(select(User)).scalars().all()
print(f"Users found in database ({len(users_in_db)} accounts):")
for u in users_in_db:
    print(f"  - Username: '{u.username:<16}' | Role: '{u.role}' | Created: {u.created_at}")

# Test known seeded default credentials against POST /api/v1/auth/login
default_credentials_to_test = [
    ("admin", "admin123"),
    ("admin", "adminpassword"),
    ("admin123", "admin123"),
    ("operator", "operator123"),
    ("operator", "operatorpassword"),
    ("operator123", "operator123"),
    ("station_manager", "adminpassword"),
]

print("\nTesting default login combinations against POST /api/v1/auth/login:")
valid_default_logins = []
for uname, pwd in default_credentials_to_test:
    resp = client.post("/api/v1/auth/login", json={"username": uname, "password": pwd})
    if resp.status_code == 200:
        role = resp.json().get("role")
        token = resp.json().get("access_token")
        valid_default_logins.append((uname, pwd, role, token))
        print(f"  [CRITICAL RISK] Default credentials active: '{uname}' / '{pwd}' -> Role: '{role}' (HTTP 200)")
    else:
        print(f"  [INFO] Failed credentials: '{uname}' / '{pwd}' -> HTTP {resp.status_code}")

# 2. RBAC Testing: station_manager vs transit_operator
print("\n[2] AUDIT: Role-Based Access Control (RBAC) Verification")
print("-" * 80)

# Generate tokens with specific roles
operator_token = create_access_token(subject="operator", role="operator")
admin_token = create_access_token(subject="admin", role="admin")
transit_operator_token = create_access_token(subject="operator", role="transit_operator")
station_manager_token = create_access_token(subject="station_manager", role="station_manager")

# Look for first available alert to test resolution
sample_alert = db.execute(select(Alert)).scalars().first()
sample_alert_id = sample_alert.id if sample_alert else 1

# Check claimed endpoints in README:
# 1. Schedule override (claimed station_manager only)
# 2. Broadcast alerts (claimed station_manager only)
# 3. Resolve alert
endpoints_to_test = [
    ("POST", "/api/v1/schedule/override", {"station_code": "222", "headway": 3.0}, "Schedule Override"),
    ("POST", "/api/v1/alerts/broadcast", {"message": "Emergency surge at Gangnam", "severity": "critical"}, "Broadcast Alerts"),
    ("POST", f"/api/v1/alerts/resolve/{sample_alert_id}", {}, f"Resolve Alert ID {sample_alert_id}"),
]

print(f"{'Endpoint':<35} | {'Role Tested':<18} | {'HTTP Status':<12} | {'Server Response Summary'}")
print("-" * 95)

for method, path, payload, desc in endpoints_to_test:
    for role_name, token in [("None (Public)", None),
                             ("transit_operator", transit_operator_token),
                             ("operator", operator_token),
                             ("admin", admin_token),
                             ("station_manager", station_manager_token)]:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        if method == "POST":
            resp = client.post(path, json=payload, headers=headers)
        else:
            resp = client.get(path, headers=headers)
        
        detail = resp.json().get("detail", "") if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:40]
        if isinstance(detail, list):
            detail = str(detail[0])
        print(f"{path:<35} | {role_name:<18} | HTTP {resp.status_code:<7} | {str(detail)[:45]}")

# 3. JWT Authentication Security Tests (Protected Endpoint: /alerts/resolve)
print("\n[3] AUDIT: JWT Security Verification on Protected Endpoint")
print("-" * 80)
resolve_path = f"/api/v1/alerts/resolve/{sample_alert_id}"

# A. No token
resp_no_token = client.post(resolve_path)
print(f"  1. No Token:             HTTP {resp_no_token.status_code} (Expected 401) -> Detail: {resp_no_token.json().get('detail')}")

# B. Expired token
expired_payload = {
    "sub": "admin",
    "role": "admin",
    "exp": datetime.now(timezone.utc) - timedelta(hours=2),
}
expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
resp_expired = client.post(resolve_path, headers={"Authorization": f"Bearer {expired_token}"})
print(f"  2. Expired Token:        HTTP {resp_expired.status_code} (Expected 401) -> Detail: {resp_expired.json().get('detail')}")

# C. Tampered signature token
tampered_token = expired_token[:-8] + "abcdefgh"
resp_tampered = client.post(resolve_path, headers={"Authorization": f"Bearer {tampered_token}"})
print(f"  3. Tampered Token:       HTTP {resp_tampered.status_code} (Expected 401) -> Detail: {resp_tampered.json().get('detail')}")

# D. Wrong secret key token
fake_secret_token = jwt.encode({"sub": "admin", "role": "admin"}, "wrong-secret-key-123", algorithm=settings.ALGORITHM)
resp_fake_secret = client.post(resolve_path, headers={"Authorization": f"Bearer {fake_secret_token}"})
print(f"  4. Wrong Secret Key:     HTTP {resp_fake_secret.status_code} (Expected 401) -> Detail: {resp_fake_secret.json().get('detail')}")

# 4. Input Validation & Edge Case Handling
print("\n[4] AUDIT: API Input Validation & Boundary Error Handling")
print("-" * 80)

input_tests = [
    ("POST", "/api/v1/predict/crowd", {"station_code": "-1", "timestamp": "2026-09-22T08:30:00Z"}, "Negative Station Code (-1)"),
    ("POST", "/api/v1/predict/crowd", {"station_code": "99999", "timestamp": "2026-09-22T08:30:00Z"}, "Non-existent Station Code (99999)"),
    ("POST", "/api/v1/predict/crowd", {"station_code": "222", "timestamp": "invalid-date-string"}, "Malformed Timestamp ('invalid-date')"),
    ("POST", "/api/v1/predict/crowd", {"station_code": "222"}, "Missing Required Field ('timestamp')"),
    ("POST", "/api/v1/predict/crowd", {}, "Empty Payload ({})"),
    ("POST", "/api/v1/schedule/delay", {"line": "Line 2", "station_code": "222", "delay_minutes": -15}, "Negative Delay Minutes (-15)"),
    ("POST", "/api/v1/schedule/delay", {"line": "Line 2", "station_code": "150", "delay_minutes": 10}, "Station Not On Specified Line (Seoul Stn 150 on Line 2)"),
    ("GET", "/api/v1/stations/INVALID_CODE_XYZ", None, "Non-existent Station Detail Lookup"),
]

print(f"{'Endpoint':<28} | {'Test Scenario':<36} | {'HTTP Status':<12} | {'API Response'}")
print("-" * 105)

for method, path, payload, desc in input_tests:
    if method == "POST":
        resp = client.post(path, json=payload)
    else:
        resp = client.get(path)
    
    body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"detail": resp.text[:30]}
    detail = body.get("detail", body)
    if isinstance(detail, list):
        detail = f"{detail[0].get('loc', '')}: {detail[0].get('msg', '')}"
    print(f"{path:<28} | {desc:<36} | HTTP {resp.status_code:<7} | {str(detail)[:45]}")

db.close()
print("\n" + "=" * 80)
print("PHASE 6 AUDIT COMPLETE")
print("=" * 80)
