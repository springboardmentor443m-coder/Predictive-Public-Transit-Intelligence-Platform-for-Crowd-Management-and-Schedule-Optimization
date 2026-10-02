import unittest
from unittest.mock import patch

import pandas as pd

from app.services.monitoring_service import (
    _pressure_level,
    _station_snapshot,
)


class MonitoringServiceTests(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame(
            [
                {
                    "Date": "2025-09-29",
                    "Hour": 18,
                    "Station": "Test Station",
                    "Ridership_entry": 100,
                    "Ridership_exit": 40,
                    "Net_Flow": 60,
                    "Is_Peak_Hour": 1,
                },
                {
                    "Date": "2025-09-30",
                    "Hour": 18,
                    "Station": "Test Station",
                    "Ridership_entry": 120,
                    "Ridership_exit": 50,
                    "Net_Flow": 70,
                    "Is_Peak_Hour": 1,
                },
                {
                    "Date": "2025-09-29",
                    "Hour": 19,
                    "Station": "Test Station",
                    "Ridership_entry": 130,
                    "Ridership_exit": 45,
                    "Net_Flow": 85,
                    "Is_Peak_Hour": 1,
                },
                {
                    "Date": "2025-09-30",
                    "Hour": 19,
                    "Station": "Test Station",
                    "Ridership_entry": 140,
                    "Ridership_exit": 55,
                    "Net_Flow": 85,
                    "Is_Peak_Hour": 1,
                },
            ]
        )

    @patch(
        "app.services.monitoring_service.predict_from_latest_data"
    )
    def test_station_snapshot(self, mock_prediction):
        mock_prediction.return_value = {
            "predicted_next_hour_ridership": 135
        }

        result = _station_snapshot(
            self.df,
            "Test Station"
        )

        self.assertIsNotNone(result)
        self.assertEqual(
            result["latest_hour"],
            19
        )

        self.assertEqual(
            result["predicted_next_hour_ridership"],
            135
        )

        self.assertIn(
            result["congestion_level"],
            {
                "LOW",
                "MODERATE",
                "HIGH",
                "CRITICAL",
            },
        )

        self.assertEqual(
            result["assessment_type"],
            "latest-historical-demand-pressure",
            )

    def test_pressure_levels(self):
        self.assertEqual(
            _pressure_level(10),
            "LOW"
        )

        self.assertEqual(
            _pressure_level(40),
            "MODERATE"
        )

        self.assertEqual(
            _pressure_level(70),
            "HIGH"
        )

        self.assertEqual(
            _pressure_level(90),
            "CRITICAL"
        )


if __name__ == "__main__":
    unittest.main()