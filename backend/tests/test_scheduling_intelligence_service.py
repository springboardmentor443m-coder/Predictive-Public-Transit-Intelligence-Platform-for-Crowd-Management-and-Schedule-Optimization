import unittest

from app.services.scheduling_intelligence_service import (
    get_station_scheduling_recommendation,
    get_network_scheduling_recommendations,
)


class TestSchedulingIntelligenceService(unittest.TestCase):

    def test_valid_station(self):
        result = get_station_scheduling_recommendation(
            "Benniganahalli"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["station"], "Benniganahalli")
        self.assertIn(
            result["priority_level"],
            ["HIGH", "MODERATE", "LOW"]
        )

    def test_invalid_station(self):
        result = get_station_scheduling_recommendation(
            "Invalid Station"
        )

        self.assertIsNone(result)

    def test_network_station_count(self):
        result = get_network_scheduling_recommendations()

        self.assertEqual(result["total_stations"], 83)

    def test_priority_counts_sum_to_total(self):
        result = get_network_scheduling_recommendations()

        total_priority_count = (
            result["high_priority_stations"]
            + result["moderate_priority_stations"]
            + result["low_priority_stations"]
        )

        self.assertEqual(
            total_priority_count,
            result["total_stations"]
        )

    def test_high_priority_headway_reduction(self):
        result = get_station_scheduling_recommendation(
            "Benniganahalli"
        )

        self.assertEqual(result["priority_level"], "HIGH")
        self.assertLess(
            result["recommended_peak_headway_minutes"],
            result["current_peak_median_headway_minutes"]
        )

    def test_headway_bounds(self):
        result = get_network_scheduling_recommendations()

        for station in result["recommendations"]:
            recommended = station[
                "recommended_peak_headway_minutes"
            ]

            self.assertGreaterEqual(recommended, 4.0)
            self.assertLessEqual(recommended, 20.0)


if __name__ == "__main__":
    unittest.main()