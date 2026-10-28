import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app.internship_app.backend.services import seasonal_analytics_service as seasonal


class SeasonalAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.history_path = Path(self.temp_dir.name) / "history.parquet"
        rows = []
        for city, station, values in (
            ("Delhi", "D1", [100.0, 120.0, None]),
            ("Delhi", "D2", [200.0, 220.0, 240.0]),
            ("Kochi", "K1", [40.0, 50.0, 60.0]),
        ):
            for timestamp, aqi in zip(
                pd.to_datetime(["2020-01-01 00:00", "2020-03-01 00:00", "2021-01-01 00:00"]),
                values,
            ):
                rows.append({
                    "City": city,
                    "StationId": station,
                    "Datetime": timestamp,
                    "AQI": aqi,
                    "PM2.5": 20.0,
                    "PM10": 40.0,
                    "NO2": 10.0,
                    "CO": 0.5,
                    "SO2": 5.0,
                    "O3": 30.0,
                    "Temperature_C": 25.0,
                    "Relative_Humidity_pct": 60.0,
                    "Wind_Speed_kmh": 8.0,
                })
        pd.DataFrame(rows).to_parquet(self.history_path)
        self.env_patch = patch.dict(os.environ, {"AQI_HISTORY_PATH": str(self.history_path)})
        self.env_patch.start()
        seasonal._read_history.cache_clear()

    def tearDown(self):
        self.env_patch.stop()
        seasonal._read_history.cache_clear()
        self.temp_dir.cleanup()

    def test_summary_aggregates_selected_city_and_year(self):
        result = seasonal.get_seasonal_summary("delhi", 2020)

        self.assertEqual(result["city"], "Delhi")
        self.assertEqual(result["year"], 2020)
        self.assertEqual(result["summary"]["stations"], 2)
        self.assertEqual(result["summary"]["year_rows"], 4)
        self.assertEqual(result["summary"]["mean_aqi"], 176.0)
        self.assertEqual([item["season"] for item in result["seasons"]], ["Winter", "Spring"])
        self.assertEqual(len(result["daily"]), 2)
        self.assertEqual(result["quality"]["AQI"], 16.7)
        self.assertEqual(result["cities"], ["Delhi", "Kochi"])

    def test_unknown_city_and_year_are_explicit_errors(self):
        with self.assertRaisesRegex(ValueError, "Unknown city"):
            seasonal.get_seasonal_summary("Atlantis")
        with self.assertRaisesRegex(ValueError, "No data"):
            seasonal.get_seasonal_summary("Kochi", 2019)

    def test_missing_history_is_an_explicit_error(self):
        missing_path = Path(self.temp_dir.name) / "missing.parquet"
        with patch.dict(os.environ, {"AQI_HISTORY_PATH": str(missing_path)}):
            with self.assertRaisesRegex(FileNotFoundError, "AQI history not found"):
                seasonal.get_seasonal_summary()

    def test_wrong_history_schema_is_an_explicit_error(self):
        invalid_path = Path(self.temp_dir.name) / "invalid.parquet"
        pd.DataFrame({"City": ["Delhi"]}).to_parquet(invalid_path)
        with patch.dict(os.environ, {"AQI_HISTORY_PATH": str(invalid_path)}):
            with self.assertRaisesRegex(RuntimeError, "missing required columns"):
                seasonal.get_seasonal_summary()

    def test_relative_history_path_resolves_from_repository_root(self):
        with patch.dict(os.environ, {"AQI_HISTORY_PATH": "data/custom_history.parquet"}):
            expected = Path(__file__).resolve().parents[3] / "data" / "custom_history.parquet"
            self.assertEqual(seasonal._data_path(), expected)


if __name__ == "__main__":
    unittest.main()
