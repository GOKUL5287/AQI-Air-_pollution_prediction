import tempfile
import unittest

import numpy as np
import pandas as pd

from src.baselines import run_baselines
from src.evaluate import save_outputs


class BaselineTests(unittest.TestCase):
    def make_features(self):
        n_rows = 130
        aqi = np.linspace(40, 120, n_rows)
        is_lockdown = np.zeros(n_rows, dtype=bool)
        is_lockdown[95:105] = True
        return pd.DataFrame(
            {
                "StationId": ["KL007"] * n_rows,
                "City": ["Kochi"] * n_rows,
                "Datetime": pd.date_range("2020-01-01", periods=n_rows, freq="h"),
                "split": ["train"] * 80 + ["gap"] * 10 + ["test"] * 40,
                "is_lockdown": is_lockdown,
                "AQI": aqi,
                "AQI_lag_1h": np.r_[np.nan, aqi[:-1]],
                "Temperature_C": np.r_[np.nan, np.linspace(20, 35, n_rows - 1)],
                "Target_AQI_24h": aqi + 4,
                "Target_AQI_48h": aqi + 8,
            }
        ).assign(
            Target_AQI_48h=lambda frame: frame["Target_AQI_48h"].mask(frame.index == 129)
        )

    def test_baselines_use_required_horizons_and_test_rows(self):
        features = self.make_features()
        predictions, metrics = run_baselines(features)

        self.assertEqual(
            set(predictions["model"]),
            {"persistence", "linear_regression", "hist_gradient_boosting"},
        )
        self.assertEqual(set(predictions["horizon_h"]), {24, 48})
        self.assertNotIn("is_lockdown", predictions.columns)

        persistence = predictions.loc[predictions["model"] == "persistence"]
        expected = features.set_index("Datetime").loc[persistence["Datetime"], "AQI"]
        np.testing.assert_allclose(persistence["y_pred"], expected.to_numpy())

        counts = metrics.query("subset == 'test_all'").groupby("horizon_h")["n_rows"]
        self.assertTrue((counts.get_group(24) == 40).all())
        self.assertTrue((counts.get_group(48) == 39).all())
        non_lockdown_counts = metrics.query("subset == 'test_excl_lockdown'").groupby(
            "horizon_h"
        )["n_rows"]
        self.assertTrue((non_lockdown_counts.get_group(24) == 30).all())
        self.assertTrue((non_lockdown_counts.get_group(48) == 29).all())
        self.assertIn("coverage", metrics.columns)
        self.assertTrue(
            metrics.loc[metrics["model"] == "persistence", "coverage"].isna().all()
        )
        boosting = predictions.loc[
            predictions["model"] == "hist_gradient_boosting"
        ]
        self.assertTrue((boosting["pi_lo"] <= boosting["pi_hi"]).all())
        self.assertTrue(boosting[["pi_lo", "pi_hi"]].notna().all().all())
        boosting_coverage = metrics.loc[
            metrics["model"] == "hist_gradient_boosting", "coverage"
        ]
        self.assertTrue(boosting_coverage.between(0, 1).all())

    def test_saves_agreed_d3_csv_outputs(self):
        predictions, metrics = run_baselines(self.make_features())
        with tempfile.TemporaryDirectory() as tmp:
            predictions_path, metrics_path = save_outputs(predictions, metrics, tmp)
            saved_predictions = pd.read_csv(predictions_path)
            saved_metrics = pd.read_csv(metrics_path)

        self.assertEqual(
            list(saved_predictions.columns),
            ["StationId", "Datetime", "horizon_h", "model", "y_true", "y_pred", "pi_lo", "pi_hi"],
        )
        self.assertEqual(
            list(saved_metrics.columns),
            ["model", "horizon_h", "subset", "n_rows", "MAE", "RMSE", "coverage"],
        )
        self.assertEqual(saved_predictions["horizon_h"].nunique(), 2)


if __name__ == "__main__":
    unittest.main()
