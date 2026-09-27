import unittest

from fastapi.testclient import TestClient

import backend.main as metroflow


class MetroFlowApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(metroflow.app)
        cls.client = cls.client_context.__enter__()
        login = cls.client.post(
            "/login",
            json={
                "email": "operator@metroflow.com",
                "password": "operator123",
                "role": "Operator",
            },
        )
        cls.token = login.json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_login_returns_access_token(self):
        self.assertTrue(self.token)

    def test_protected_endpoint_rejects_missing_token(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 401)

    def test_protected_endpoint_accepts_valid_token(self):
        response = self.client.get("/api/v1/health", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_operations_summary_is_available(self):
        response = self.client.get("/api/v1/operations/summary", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("trains", response.json())
        self.assertIn("alerts", response.json())

    def test_telemetry_can_be_ingested_and_read(self):
        payload = {
            "active_services": 1,
            "trains": [
                {
                    "service": "TEST-1",
                    "line": "Test Line",
                    "current_station": "Test Station",
                    "status": "On time",
                    "next_arrival": "2 min",
                }
            ],
            "alerts": [],
            "schedule": {
                "line": "Test Line",
                "station": "Test Station",
                "recommended_headway_minutes": 5,
                "confidence": 90,
            },
        }
        response = self.client.post(
            "/api/v1/operations/telemetry",
            json=payload,
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        summary = self.client.get("/api/v1/operations/summary", headers=self.headers)
        self.assertEqual(summary.json()["trains"][0]["service"], "TEST-1")
        metroflow.operations_collection.delete_many({"source": "telemetry"})


if __name__ == "__main__":
    unittest.main()
