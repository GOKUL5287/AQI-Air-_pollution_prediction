"""Read and summarize the shared station-hour AQI history for the web dashboard."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

POLLUTANTS = ["PM2.5", "PM10", "NO2", "CO", "SO2", "O3"]
WEATHER = ["Temperature_C", "Relative_Humidity_pct", "Wind_Speed_kmh"]
DATA_COLUMNS = ["City", "StationId", "Datetime", "AQI", *POLLUTANTS, *WEATHER]
SEASONS = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Autumn", 10: "Autumn", 11: "Autumn",
}
SEASON_ORDER = ["Winter", "Spring", "Summer", "Autumn"]


def _data_path() -> Path:
    repo_root = Path(__file__).resolve().parents[4]
    configured = os.environ.get("AQI_HISTORY_PATH")
    if configured:
        configured_path = Path(configured).expanduser()
        return configured_path if configured_path.is_absolute() else repo_root / configured_path
    return repo_root / "data" / "station_hour_merged.parquet"


@lru_cache(maxsize=2)
def _read_history(path: str, modified_ns: int, size: int) -> pd.DataFrame:
    del modified_ns, size
    return pd.read_parquet(path, columns=DATA_COLUMNS)


def _number(value: Any) -> Optional[float]:
    if pd.isna(value):
        return None
    return float(value)


def get_seasonal_summary(city: Optional[str] = None, year: Optional[int] = None) -> Dict[str, Any]:
    path = _data_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"AQI history not found at {path}. Set AQI_HISTORY_PATH to the station-hour Parquet file."
        )

    try:
        stat = path.stat()
        available_columns = set(pq.ParquetFile(path).schema.names)
        missing_columns = sorted(set(DATA_COLUMNS) - available_columns)
        if missing_columns:
            raise ValueError(
                f"AQI history is missing required columns: {', '.join(missing_columns)}"
            )
        history = _read_history(str(path), stat.st_mtime_ns, stat.st_size)
    except (OSError, ValueError, ImportError, pa.ArrowException) as error:
        raise RuntimeError(f"Could not read AQI history at {path}: {error}") from error

    if history.empty:
        raise ValueError(f"AQI history at {path} contains no rows.")

    available_cities = sorted(history["City"].dropna().astype(str).unique(), key=str.casefold)
    if not available_cities:
        raise ValueError("AQI history contains no city names.")
    selected_city = city or ("Delhi" if "Delhi" in available_cities else available_cities[0])
    matches = {name.casefold(): name for name in available_cities}
    selected_city = matches.get(selected_city.casefold())
    if selected_city is None:
        raise ValueError(f"Unknown city. Choose one of: {', '.join(available_cities)}")

    city_rows = history.loc[history["City"].astype(str) == selected_city].copy()
    city_rows["Datetime"] = pd.to_datetime(city_rows["Datetime"], errors="coerce")
    city_rows = city_rows.dropna(subset=["Datetime"])
    if city_rows.empty:
        raise ValueError(f"No timestamped AQI history is available for {selected_city}.")

    city_rows["Year"] = city_rows["Datetime"].dt.year
    years = sorted(int(value) for value in city_rows["Year"].dropna().unique())
    selected_year = int(year) if year is not None else years[-1]
    if selected_year not in years:
        raise ValueError(f"No data for {selected_city} in {selected_year}. Available years: {years}")

    city_rows["Season"] = city_rows["Datetime"].dt.month.map(SEASONS)
    city_rows["Month"] = city_rows["Datetime"].dt.month
    city_rows["Day"] = city_rows["Datetime"].dt.floor("D")

    monthly_values = city_rows.groupby(
        [pd.Grouper(key="Datetime", freq="MS")], observed=True
    ).agg({"AQI": "mean", **{column: "mean" for column in POLLUTANTS + WEATHER}})
    monthly_counts = city_rows.groupby(pd.Grouper(key="Datetime", freq="MS"))["AQI"].count()
    monthly = []
    for timestamp, row in monthly_values.iterrows():
        item = {
            "date": timestamp.strftime("%Y-%m-%d"),
            "year": int(timestamp.year),
            "month": int(timestamp.month),
            "season": SEASONS[int(timestamp.month)],
            "observations": int(monthly_counts.get(timestamp, 0)),
        }
        item.update({column: _number(row[column]) for column in ["AQI", *POLLUTANTS, *WEATHER]})
        monthly.append(item)

    seasonal_means = city_rows.groupby("Season", observed=True)[
        ["AQI", *POLLUTANTS, *WEATHER]
    ].mean()
    overall_pollutant_means = city_rows[POLLUTANTS].mean()
    seasons = []
    for season in SEASON_ORDER:
        if season not in seasonal_means.index:
            continue
        row = seasonal_means.loc[season]
        item = {"season": season}
        item.update({column: _number(row[column]) for column in ["AQI", *POLLUTANTS, *WEATHER]})
        item["pollutant_index"] = {
            pollutant: (
                float(row[pollutant] / overall_pollutant_means[pollutant] * 100)
                if pd.notna(overall_pollutant_means[pollutant]) and overall_pollutant_means[pollutant] != 0
                and pd.notna(row[pollutant])
                else None
            )
            for pollutant in POLLUTANTS
        }
        seasons.append(item)

    year_rows = city_rows.loc[city_rows["Year"] == selected_year].copy()
    daily_values = year_rows.groupby("Day").agg({"AQI": "mean"})["AQI"]
    daily_counts = year_rows.groupby("Day")["AQI"].count()
    daily = [
        {
            "date": date.strftime("%Y-%m-%d"),
            "aqi": _number(value),
            "observations": int(daily_counts.get(date, 0)),
        }
        for date, value in daily_values.items()
    ]

    quality = {
        column: round(float(city_rows[column].isna().mean() * 100), 1)
        for column in ["AQI", *POLLUTANTS, *WEATHER]
    }
    return {
        "city": selected_city,
        "year": selected_year,
        "cities": available_cities,
        "years": years,
        "summary": {
            "rows": int(len(city_rows)),
            "stations": int(city_rows["StationId"].nunique()),
            "start": city_rows["Datetime"].min().isoformat(),
            "end": city_rows["Datetime"].max().isoformat(),
            "mean_aqi": _number(city_rows["AQI"].mean()),
            "year_rows": int(len(year_rows)),
        },
        "quality": quality,
        "monthly": monthly,
        "seasons": seasons,
        "daily": daily,
    }
