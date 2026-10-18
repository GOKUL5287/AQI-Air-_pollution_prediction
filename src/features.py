"""Feature engineering for D2 (features_v1.parquet). Owner: Gokul."""
import numpy as np
import pandas as pd

HOUR = pd.Timedelta(hours=1)
TARGET_H = [24, 48]          # forecast horizons (hours ahead)
LAGS_H = [1, 6, 12, 24, 48]  # how far back the lag features look
ROLL_H = [6, 12, 24]         # rolling-mean window sizes (hours)


def assert_contiguous(df: pd.DataFrame,
                      station_col: str = "StationId",
                      time_col: str = "Datetime") -> None:
    """Assert each station's rows are sorted, unique and exactly 1 hour apart.

    groupby(station).shift(24) moves 24 *rows*. That only equals 24 *hours*
    if there are no holes in the hourly timeline. Run this on the FULL table,
    before any row is dropped.
    """
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        raise TypeError(f"{time_col} must be datetime, got {df[time_col].dtype}")

    sorted_df = df.sort_values([station_col, time_col])
    assert sorted_df.index.equals(df.index), "Rows are not sorted by (StationId, Datetime)."

    n_dup = int(df.duplicated([station_col, time_col]).sum())
    assert n_dup == 0, f"{n_dup} duplicate (StationId, Datetime) pairs."

    step = df.groupby(station_col, sort=False)[time_col].diff()
    bad = step.notna() & (step != HOUR)
    if bad.any():
        stations = df.loc[bad, station_col].unique()[:5].tolist()
        raise AssertionError(f"{int(bad.sum())} steps != 1h. First stations affected: {stations}")

    print(f"OK: {df[station_col].nunique()} station(s), {len(df):,} rows, "
          f"hourly-contiguous within every station.")


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Targets, lags, rolling means and calendar/wind encodings for D2.

    Everything is computed per station on the FULL sorted table. Rows with
    missing AQI are dropped only at the very end. No imputation anywhere.
    """
    assert_contiguous(df)            # row shift must equal hour shift
    out = df.copy()
    aqi = out.groupby("StationId", sort=False)["AQI"]

    # Targets: AQI at the same station 24h / 48h LATER (negative shift)
    for h in TARGET_H:
        out[f"Target_AQI_{h}h"] = aqi.shift(-h)

    # Lags: AQI h hours EARLIER (positive shift)
    for h in LAGS_H:
        out[f"AQI_lag_{h}h"] = aqi.shift(h)

    # Rolling means over the past w hours (including the current hour)
    for w in ROLL_H:
        out[f"AQI_rolling_mean_{w}h"] = aqi.transform(
            lambda s: s.rolling(window=w, min_periods=w // 2).mean()
        )

    # Calendar features as sin/cos so the cycle wraps around
    t = out["Datetime"]
    out["Hour_sin"] = np.sin(2 * np.pi * t.dt.hour / 24)
    out["Hour_cos"] = np.cos(2 * np.pi * t.dt.hour / 24)
    out["DayOfWeek_sin"] = np.sin(2 * np.pi * t.dt.dayofweek / 7)
    out["DayOfWeek_cos"] = np.cos(2 * np.pi * t.dt.dayofweek / 7)
    out["Month_sin"] = np.sin(2 * np.pi * t.dt.month / 12)
    out["Month_cos"] = np.cos(2 * np.pi * t.dt.month / 12)
    out["DayOfYear"] = t.dt.dayofyear

    # Wind direction: degrees -> radians -> sin/cos
    rad = np.deg2rad(out["Wind_Direction_deg"])
    out["Wind_Dir_sin"] = np.sin(rad)
    out["Wind_Dir_cos"] = np.cos(rad)

    # LAST: keep only rows where AQI is present
    out = out[out["AQI"].notna()].reset_index(drop=True)
    return out