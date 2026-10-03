import unittest

from app.services.operations_service import (
    get_station_operations_summary,
    get_network_operations_summary
)


class TestOperationsService(unittest.TestCase):

    def test_station_operations_summary(self):
        result = get_station_operations_summary(
            "Benniganahalli",
            "2025-09-30",
            18
        )

        self.assertIsNotNone(result)
        self.assertEqual(
            result["station"],
            "Benniganahalli"
        )

        self.assertIn("monitoring", result)
        self.assertIn("alerts", result)
        self.assertIn("scheduling", result)

    def test_network_operations_summary(self):
        result = get_network_operations_summary(
            "2025-09-30",
            18
        )

        self.assertEqual(
            result["stations_monitored"],
            83
        )

        self.assertIn(
            "pressure_counts",
            result
        )

        self.assertIn(
            "monitoring",
            result
        )

        self.assertIn(
            "alerts",
            result
        )

        self.assertIn(
            "scheduling",
            result
        )


if __name__ == "__main__":
    unittest.main()