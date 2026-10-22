import unittest

import numpy as np
import pandas as pd

from src.lstm import WINDOW, make_windows, split_windows
from src.prophet_model import prophet_frames


class NoLeakageTests(unittest.TestCase):
    def make_features(self):
        n_rows = 200
        aqi = np.linspace(40, 120, n_rows)
        frame = pd.DataFrame(
            {
                "StationId": ["KL007"] * n_rows,
                "City": ["Kochi"] * n_rows,
                "Datetime": pd.date_range("2020-01-01", periods=n_rows, freq="h"),
                "split": ["train"] * 120 + ["gap"] * 48 + ["test"] * 32,
                "is_lockdown": False,
                "AQI": aqi,
                "Temperature_C": np.linspace(20, 35, n_rows),
                "Relative_Humidity_pct": 60,
                "Wind_Speed_kmh": 5.0,
                "Wind_Dir_sin": 0.0,
                "Wind_Dir_cos": 1.0,
                "Target_AQI_24h": aqi + 4,
                "Target_AQI_48h": aqi + 8,
            }
        )
        # A time hole inside train: no window may span it.
        return frame.drop(index=60).reset_index(drop=True)

    def test_lstm_training_windows_only_touch_train_rows(self):
        df, ends = make_windows(self.make_features())
        train_ends, _ = split_windows(df, ends)
        self.assertGreater(len(train_ends), 0)
        rows = train_ends[:, None] + np.arange(-WINDOW + 1, 1)
        self.assertTrue((df["split"].to_numpy()[rows] == "train").all())
        span = df["Datetime"].to_numpy()[rows[:, -1]] - df["Datetime"].to_numpy()[rows[:, 0]]
        self.assertTrue((span == np.timedelta64(WINDOW - 1, "h")).all())

    def test_prophet_training_rows_only_use_train_origins(self):
        df = self.make_features()
        train_times = set(df.loc[df["split"] == "train", "Datetime"])
        for horizon in (24, 48):
            train, _ = prophet_frames(df, horizon)
            self.assertGreater(len(train), 0)
            self.assertTrue(train["Datetime"].isin(train_times).all())
            self.assertTrue((train["split"] == "train").all())


if __name__ == "__main__":
    unittest.main()
