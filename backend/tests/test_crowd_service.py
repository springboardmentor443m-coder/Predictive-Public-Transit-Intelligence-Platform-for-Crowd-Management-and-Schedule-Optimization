import unittest
from unittest.mock import patch

import pandas as pd

from app.services.crowd_service import (
    _build_station_hour_demand,
    get_station_crowd_status,
    get_station_crowd_heatmap,
    get_station_demand_pressure,
    get_station_flow,
)


class CrowdServiceTests(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame(
            [
                {"Date": "2025-09-01", "Hour": 8, "Station": "Alpha", "Ridership": 10},
                {"Date": "2025-09-01", "Hour": 9, "Station": "Alpha", "Ridership": 20},
                {"Date": "2025-09-01", "Hour": 10, "Station": "Alpha", "Ridership": 30},
                {"Date": "2025-09-01", "Hour": 8, "Station": "Beta", "Ridership": 100},
                {"Date": "2025-09-01", "Hour": 9, "Station": "Beta", "Ridership": 200},
                {"Date": "2025-09-01", "Hour": 10, "Station": "Beta", "Ridership": 300},
            ]
        )

    @patch("app.services.crowd_service.load_ridership_data")
    def test_demand_classification_uses_station_percentiles(self, mock_load):
        mock_load.return_value = self.df.copy()

        result = _build_station_hour_demand()

        alpha = result[result["Station"] == "Alpha"].sort_values("Hour")
        self.assertEqual(
            alpha["Demand Status"].tolist(),
            ["Low", "Moderate", "High"],
        )

        beta = result[result["Station"] == "Beta"].sort_values("Hour")
        self.assertEqual(
            beta["Demand Status"].tolist(),
            ["Low", "Moderate", "High"],
        )

    @patch("app.services.crowd_service.load_ridership_data")
    def test_crowd_status_returns_expected_fields(self, mock_load):
        mock_load.return_value = self.df.copy()

        result = get_station_crowd_status()

        self.assertEqual(len(result), 6)
        self.assertTrue(
            all(
                {"Station", "Hour", "Ridership", "Demand Status"}.issubset(row)
                for row in result
            )
        )

    @patch("app.services.crowd_service.load_ridership_data")
    def test_heatmap_returns_sorted_station_hour_records(self, mock_load):
        mock_load.return_value = self.df.copy()

        result = get_station_crowd_heatmap()

        self.assertEqual(len(result), 6)
        self.assertNotIn("P25", result[0])
        self.assertNotIn("P75", result[0])

        keys = [(row["Station"], row["Hour"]) for row in result]
        self.assertEqual(keys, sorted(keys))

    @patch("app.services.crowd_service.load_ridership_data")
    def test_demand_pressure_is_bounded(self, mock_load):
        mock_load.return_value = self.df.copy()

        result = get_station_demand_pressure()

        for row in result:
            self.assertGreaterEqual(row["Demand Pressure"], 0)
            self.assertLessEqual(row["Demand Pressure"], 100)
            self.assertIn(
                "Station Average Ridership",
                row,
            )
            self.assertIn(
                "Demand vs Average (%)",
                row,
            )

    @patch("app.services.crowd_service.pd.read_csv")
    @patch("app.services.crowd_service.load_ridership_data")
    def test_passenger_flow_uses_only_matching_records(
        self, mock_load, mock_read_csv
    ):
        entries = pd.DataFrame(
            [
                {
                    "Date": pd.Timestamp("2025-09-01"),
                    "Hour": 8,
                    "Station": "Alpha",
                    "Ridership": 100,
                },
                {
                    "Date": pd.Timestamp("2025-09-01"),
                    "Hour": 9,
                    "Station": "Alpha",
                    "Ridership": 120,
                },
            ]
        )

        exits = pd.DataFrame(
            [
                {
                    "Date": "2025-09-01",
                    "Hour": 8,
                    "Station": "Alpha",
                    "Ridership": 40,
                },
                {
                    "Date": "2025-09-01",
                    "Hour": 9,
                    "Station": "Alpha",
                    "Ridership": 50,
                },
                {
                    "Date": "2025-09-01",
                    "Hour": 10,
                    "Station": "Alpha",
                    "Ridership": 70,
                },
            ]
        )

        mock_load.return_value = entries
        mock_read_csv.return_value = exits

        result = get_station_flow()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Station"], "Alpha")
        self.assertEqual(result[0]["Ridership_entry"], 220)
        self.assertEqual(result[0]["Ridership_exit"], 90)
        self.assertEqual(result[0]["Net Flow"], 130)


if __name__ == "__main__":
    unittest.main()
