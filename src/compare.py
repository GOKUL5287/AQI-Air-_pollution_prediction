"""Compare persistence, HGB, LSTM and Prophet on the test rows all four predict (D3 v2)."""

import pandas as pd

from src.data_loader import data_dir
from src.evaluate import evaluate_predictions, save_outputs
from src.split import LOCKDOWN_START

KEYS = ["StationId", "Datetime", "horizon_h"]
V1_MODELS = ["persistence", "hist_gradient_boosting"]
NO_PROPHET = V1_MODELS + ["lstm"]


def compare(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep rows predicted by every model, then compute MAE/RMSE per subset and horizon."""
    n_models = predictions.groupby(KEYS)["model"].transform("nunique")
    common = predictions[n_models == predictions["model"].nunique()]
    metrics = evaluate_predictions(common.assign(is_lockdown=common["Datetime"] >= LOCKDOWN_START))
    return common, metrics


def main() -> tuple[pd.DataFrame, pd.DataFrame]:
    processed = data_dir() / "processed"
    v1 = pd.read_csv(processed / "predictions_v1.csv", parse_dates=["Datetime"])
    predictions = pd.concat(
        [
            v1[v1["model"].isin(V1_MODELS)],
            pd.read_parquet(processed / "predictions_lstm.parquet"),
            pd.read_parquet(processed / "predictions_prophet.parquet"),
        ],
        ignore_index=True,
    )
    common, metrics = compare(predictions)
    save_outputs(common, metrics, processed, version="v2")
    _, metrics_no_prophet = compare(predictions[predictions["model"].isin(NO_PROPHET)])
    metrics_no_prophet.to_csv(processed / "metrics_v2_excl_prophet.csv", index=False)
    return metrics, metrics_no_prophet


if __name__ == "__main__":
    for table in main():
        print(table.to_string(index=False))
