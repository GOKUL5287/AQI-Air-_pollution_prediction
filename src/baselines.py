"""Persistence, linear-regression and histogram-gradient-boosting baselines."""

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline

from src.evaluate import evaluate_predictions

HORIZONS = (24, 48)
EXCLUDED_FEATURES = {
    "StationId",
    "City",
    "Datetime",
    "Target_AQI_24h",
    "Target_AQI_48h",
    "split",
    "is_lockdown",
}
def _feature_columns(df: pd.DataFrame) -> list[str]:
    columns = [column for column in df.columns if column not in EXCLUDED_FEATURES]
    non_numeric = [column for column in columns if not pd.api.types.is_numeric_dtype(df[column])]
    if non_numeric:
        raise TypeError(f"Model features must be numeric: {non_numeric}")
    if not columns:
        raise ValueError("No D2 model features were found.")
    return columns


def _make_predictions_for_horizon(
    df: pd.DataFrame, horizon: int, feature_columns: list[str]
) -> list[pd.DataFrame]:
    target = f"Target_AQI_{horizon}h"
    if target not in df:
        raise ValueError(f"D2 is missing the required target column {target!r}.")

    train = df.loc[(df["split"] == "train") & df[target].notna()]
    test = df.loc[(df["split"] == "test") & df[target].notna()]
    if train.empty:
        raise ValueError(f"No training rows with a valid {target} target.")
    if test.empty:
        raise ValueError(f"No test rows with a valid {target} target.")

    train_x = train[feature_columns]
    test_x = test[feature_columns]
    train_y = train[target].to_numpy(dtype=float)
    test_y = test[target].to_numpy(dtype=float)

    predictions = []

    if train["AQI"].isna().any() or test["AQI"].isna().any():
        raise ValueError("Persistence requires non-missing current AQI on train and test rows.")
    predictions.append(
        pd.DataFrame(
            {
                "StationId": test["StationId"].to_numpy(),
                "Datetime": test["Datetime"].to_numpy(),
                "horizon_h": horizon,
                "model": "persistence",
                "y_true": test_y,
                "y_pred": test["AQI"].to_numpy(dtype=float),
                "is_lockdown": test["is_lockdown"].to_numpy(dtype=bool),
            }
        )
    )

    linear = make_pipeline(SimpleImputer(strategy="median"), LinearRegression())
    linear.fit(train_x, train_y)
    predictions.append(
        pd.DataFrame(
            {
                "StationId": test["StationId"].to_numpy(),
                "Datetime": test["Datetime"].to_numpy(),
                "horizon_h": horizon,
                "model": "linear_regression",
                "y_true": test_y,
                "y_pred": linear.predict(test_x),
                "is_lockdown": test["is_lockdown"].to_numpy(dtype=bool),
            }
        )
    )

    boosting = HistGradientBoostingRegressor(random_state=42)
    boosting.fit(train_x, train_y)
    boosting_prediction = boosting.predict(test_x)

    lower_model = HistGradientBoostingRegressor(
        loss="quantile", quantile=0.05, random_state=42
    )
    upper_model = HistGradientBoostingRegressor(
        loss="quantile", quantile=0.95, random_state=42
    )
    lower_model.fit(train_x, train_y)
    upper_model.fit(train_x, train_y)
    lower = lower_model.predict(test_x)
    upper = upper_model.predict(test_x)

    predictions.append(
        pd.DataFrame(
            {
                "StationId": test["StationId"].to_numpy(),
                "Datetime": test["Datetime"].to_numpy(),
                "horizon_h": horizon,
                "model": "hist_gradient_boosting",
                "y_true": test_y,
                "y_pred": boosting_prediction,
                "pi_lo": np.minimum(lower, upper),
                "pi_hi": np.maximum(lower, upper),
                "is_lockdown": test["is_lockdown"].to_numpy(dtype=bool),
            }
        )
    )
    return predictions


def run_baselines(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit each baseline on train rows and evaluate target-valid test rows."""
    required = {"StationId", "Datetime", "AQI", "split", "is_lockdown"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"D2 is missing required columns: {sorted(missing)}")

    feature_columns = _feature_columns(df)
    prediction_parts = [
        part
        for horizon in HORIZONS
        for part in _make_predictions_for_horizon(df, horizon, feature_columns)
    ]
    internal_predictions = pd.concat(prediction_parts, ignore_index=True)
    metrics = evaluate_predictions(internal_predictions)
    predictions = internal_predictions.drop(columns="is_lockdown")
    return predictions, metrics
