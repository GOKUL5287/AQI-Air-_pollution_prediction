"""Evaluation and persistence helpers for the D3 baseline outputs."""

from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

PREDICTION_COLUMNS = [
    "StationId",
    "Datetime",
    "horizon_h",
    "model",
    "y_true",
    "y_pred",
]
INTERVAL_COLUMNS = ["pi_lo", "pi_hi"]


def evaluate_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    """Calculate test metrics for all rows and for non-lockdown rows."""
    required = {"model", "horizon_h", "y_true", "y_pred", "is_lockdown"}
    missing = required.difference(predictions.columns)
    if missing:
        raise ValueError(f"Predictions are missing required columns: {sorted(missing)}")

    has_interval_columns = {"pi_lo", "pi_hi"}.issubset(predictions.columns)
    metric_rows = []
    for (model, horizon), group in predictions.groupby(
        ["model", "horizon_h"], sort=True, observed=True
    ):
        has_intervals = has_interval_columns and group[["pi_lo", "pi_hi"]].notna().all(
            axis=1
        ).any()
        for subset, selected in (
            ("test_all", group),
            ("test_excl_lockdown", group.loc[~group["is_lockdown"].astype(bool)]),
        ):
            y_true = selected["y_true"].to_numpy(dtype=float)
            y_pred = selected["y_pred"].to_numpy(dtype=float)
            row = {
                "model": model,
                "horizon_h": int(horizon),
                "subset": subset,
                "n_rows": len(selected),
                "MAE": float(mean_absolute_error(y_true, y_pred)) if len(selected) else np.nan,
                "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred)))
                if len(selected)
                else np.nan,
            }
            if has_intervals:
                if len(selected):
                    covered = (
                        (selected["y_true"] >= selected["pi_lo"])
                        & (selected["y_true"] <= selected["pi_hi"])
                    )
                    row["coverage"] = float(covered.mean())
                else:
                    row["coverage"] = np.nan
            metric_rows.append(row)

    return pd.DataFrame(metric_rows)


def save_outputs(
    predictions: pd.DataFrame,
    metrics: pd.DataFrame,
    output_dir: Union[str, Path],
    version: str = "v1",
) -> tuple[Path, Path]:
    """Write the agreed D3 CSV files into the processed data directory."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prediction_columns = PREDICTION_COLUMNS + [
        column for column in INTERVAL_COLUMNS if column in predictions.columns
    ]
    missing = set(PREDICTION_COLUMNS).difference(predictions.columns)
    if missing:
        raise ValueError(f"Predictions are missing output columns: {sorted(missing)}")

    predictions_path = output_dir / f"predictions_{version}.csv"
    metrics_path = output_dir / f"metrics_{version}.csv"
    predictions[prediction_columns].to_csv(predictions_path, index=False)
    metrics.to_csv(metrics_path, index=False)
    return predictions_path, metrics_path
