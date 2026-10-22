"""Per-station, per-horizon Prophet with AQI and weather regressors known at origin time."""

import logging
import os
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
from prophet import Prophet

from src.baselines import HORIZONS

REGRESSORS = [
    "AQI",
    "Temperature_C",
    "Relative_Humidity_pct",
    "Wind_Speed_kmh",
    "Wind_Dir_sin",
    "Wind_Dir_cos",
]


def _silence():
    logging.getLogger("cmdstanpy").disabled = True
    logging.getLogger("prophet").setLevel(logging.WARNING)


def prophet_frames(station_df: pd.DataFrame, horizon: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Origin rows -> (train, test) with ds = origin + h and y = Target_AQI_h."""
    target = f"Target_AQI_{horizon}h"
    rows = station_df[station_df[target].notna()]
    frame = rows[["StationId", "Datetime", "split"] + REGRESSORS].assign(
        ds=rows["Datetime"] + pd.Timedelta(hours=horizon), y=rows[target]
    )
    return frame[frame["split"] == "train"], frame[frame["split"] == "test"]


def _fit_station(station_df: pd.DataFrame) -> pd.DataFrame:
    _silence()
    parts = []
    for horizon in HORIZONS:
        train, test = prophet_frames(station_df, horizon)
        if len(train) < 2 or test.empty:
            continue
        regressors = [r for r in REGRESSORS if train[r].notna().any() and train[r].std() > 0]
        fill = train[regressors].median()
        model = Prophet(
            growth="flat", daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False
        )
        for regressor in regressors:
            model.add_regressor(regressor)
        model.fit(train[["ds", "y"] + regressors].fillna(fill))
        forecast = model.predict(test[["ds"] + regressors].fillna(fill))
        parts.append(
            pd.DataFrame(
                {
                    "StationId": test["StationId"].to_numpy(),
                    "Datetime": test["Datetime"].to_numpy(),
                    "horizon_h": horizon,
                    "model": "prophet",
                    "y_true": test["y"].to_numpy(dtype=float),
                    "y_pred": forecast["yhat"].to_numpy(),
                }
            )
        )
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def run_prophet(df: pd.DataFrame, workers: int | None = None) -> pd.DataFrame:
    """Fit train rows and predict test rows for every station, in parallel processes."""
    _silence()
    columns = ["StationId", "Datetime", "split"] + [f"Target_AQI_{h}h" for h in HORIZONS] + REGRESSORS
    stations = [group for _, group in df[columns].groupby("StationId", sort=True)]
    with ProcessPoolExecutor(workers or os.cpu_count()) as pool:
        return pd.concat(pool.map(_fit_station, stations), ignore_index=True)


if __name__ == "__main__":
    from src.data_loader import data_dir, load_features

    run_prophet(load_features()).to_parquet(
        data_dir() / "processed" / "predictions_prophet.parquet", index=False
    )
