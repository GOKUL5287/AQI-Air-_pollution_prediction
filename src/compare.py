"""Compare persistence, HGB, LSTM and Prophet on the test rows all four predict (D3 v2)."""

import pandas as pd

from src.data_loader import data_dir
from src.evaluate import evaluate_predictions, save_outputs
from src.split import LOCKDOWN_START

KEYS = ["StationId", "Datetime", "horizon_h"]
V1_MODELS = ["persistence", "hist_gradient_boosting"]


def compare(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep rows predicted by every model, then compute MAE/RMSE per subset and horizon."""
    n_models = predictions.groupby(KEYS)["model"].transform("nunique")
    common = predictions[n_models == predictions["model"].nunique()]
    metrics = evaluate_predictions(common.assign(is_lockdown=common["Datetime"] >= LOCKDOWN_START))
    return common, metrics


def main() -> pd.DataFrame:
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
    return metrics


if __name__ == "__main__":
    print(main().to_string(index=False))
