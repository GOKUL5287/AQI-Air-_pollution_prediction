"""
Loads the project's data files.

The data folder is configurable so the same code works on every team member's Colab:

    os.environ["AQI_DATA_DIR"] = "/content/drive/MyDrive/AQI_Project_Data"

AQI_DATA_DIR must point at the folder that contains raw/, processed/ and samples/.
If it is not set, the loader falls back to <repo>/data.

Small reference files (city_coordinates.csv, station_coverage.csv) are committed
to the repo in data/reference/ and are always read from there.

Owner: Anand. Others ask for changes instead of editing this file.
"""

import os
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("AQI_DATA_DIR", REPO_ROOT / "data"))


def data_dir() -> Path:
    """Folder holding raw/, processed/ and samples/."""
    return DATA_DIR


def _check(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found.\n"
            f"AQI_DATA_DIR is {os.environ.get('AQI_DATA_DIR', 'not set')!r}. "
            "On Colab, check that the shared Drive folder is added to My Drive as a "
            "shortcut named exactly 'AQI_Project_Data', and that the file owner has "
            "created this file."
        )
    return path


# ---------------------------------------------------------------- raw/
def load_station_hour() -> pd.DataFrame:
    return pd.read_csv(_check(data_dir() / "raw" / "station_hour.csv"), low_memory=False)


def load_station_day() -> pd.DataFrame:
    return pd.read_csv(_check(data_dir() / "raw" / "station_day.csv"))


def load_city_hour() -> pd.DataFrame:
    return pd.read_csv(_check(data_dir() / "raw" / "city_hour.csv"))


def load_city_day() -> pd.DataFrame:
    return pd.read_csv(_check(data_dir() / "raw" / "city_day.csv"))


def load_stations() -> pd.DataFrame:
    return pd.read_csv(_check(data_dir() / "raw" / "stations.csv"))


def load_weather() -> pd.DataFrame:
    return pd.read_csv(
        _check(data_dir() / "raw" / "openmeteo_india_weather.csv"),
        parse_dates=["Datetime"],
    )


# ---------------------------------------------------------------- processed/
def load_merged(sample: bool = False) -> pd.DataFrame:
    """D1: one row per station-hour. sample=True returns the KL007 sample only."""
    if sample:
        return pd.read_csv(
            _check(data_dir() / "samples" / "KL007_sample.csv"),
            parse_dates=["Datetime"],
        )
    return pd.read_parquet(_check(data_dir() / "processed" / "station_hour_merged.parquet"))


def load_features() -> pd.DataFrame:
    """D2: past-only features, targets and the train/gap/test split label."""
    return pd.read_parquet(_check(data_dir() / "processed" / "features_v1.parquet"))


def load_predictions() -> pd.DataFrame:
    """D3: predictions for every model and horizon."""
    return pd.read_csv(
        _check(data_dir() / "processed" / "predictions_v1.csv"),
        parse_dates=["Datetime"],
    )


def load_metrics() -> pd.DataFrame:
    """D3: MAE and RMSE per model, horizon and subset."""
    return pd.read_csv(_check(data_dir() / "processed" / "metrics_v1.csv"))


def load_dominant() -> pd.DataFrame:
    """Sub-indices and dominant pollutant per station-hour."""
    return pd.read_parquet(_check(data_dir() / "processed" / "dominant_pollutant.parquet"))


# ---------------------------------------------------------------- data/reference/ (in Git)
def load_city_coordinates() -> pd.DataFrame:
    return pd.read_csv(_check(REPO_ROOT / "data" / "reference" / "city_coordinates.csv"))


def load_station_coverage() -> pd.DataFrame:
    return pd.read_csv(_check(REPO_ROOT / "data" / "reference" / "station_coverage.csv"))
