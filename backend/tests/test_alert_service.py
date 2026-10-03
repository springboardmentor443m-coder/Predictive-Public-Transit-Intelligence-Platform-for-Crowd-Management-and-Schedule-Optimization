import unittest

from app.services.alert_service import (
    generate_station_alerts,
    generate_network_alerts,
)


class TestAlertService(unittest.TestCase):

    def test_critical_station_alert(self):
        result = generate_station_alerts(
            "Mahatma Gandhi Road",
            "2025-09-30",
            18
        )

        self.assertEqual(
            result["station"],
            "Mahatma Gandhi Road"
        )

        self.assertGreater(
            result["alert_count"],
            0
        )

        critical_alerts = [
            alert
            for alert in result["alerts"]
            if alert["severity"] == "CRITICAL"
        ]

        self.assertGreater(
            len(critical_alerts),
            0
        )

    def test_prediction_deviation_alert(self):
        result = generate_station_alerts(
            "Attiguppe",
            "2025-09-30",
            18
        )

        deviation_alerts = [
            alert
            for alert in result["alerts"]
            if alert["alert_type"] == "prediction_deviation"
        ]

        self.assertGreater(
            len(deviation_alerts),
            0
        )

        self.assertGreaterEqual(
            deviation_alerts[0]["prediction_error_percentage"],
            20
        )

    def test_network_alert_generation(self):
        result = generate_network_alerts(
            "2025-09-30",
            18
        )

        self.assertEqual(
            result["monitoring_date"],
            "2025-09-30"
        )

        self.assertEqual(
            result["monitoring_hour"],
            18
        )

        self.assertGreater(
            result["total_alerts"],
            0
        )

        self.assertEqual(
            sum(result["severity_counts"].values()),
            result["total_alerts"]
        )

    def test_network_contains_mahatma_gandhi_road_alert(self):
        result = generate_network_alerts(
            "2025-09-30",
            18
        )

        station_alerts = [
            alert
            for alert in result["alerts"]
            if alert["station"] == "Mahatma Gandhi Road"
        ]

        self.assertGreater(
            len(station_alerts),
            0
        )

        self.assertTrue(
            any(
                alert["severity"] == "CRITICAL"
                for alert in station_alerts
            )
        )

    def test_invalid_station(self):
        result = generate_station_alerts(
            "Invalid Station",
            "2025-09-30",
            18
        )

        self.assertEqual(
            result["station"],
            "Invalid Station"
        )

        self.assertEqual(
            result["alerts"],
            []
        )

        self.assertEqual(
            result["message"],
            "No monitoring data found."
        )


if __name__ == "__main__":
    unittest.main()