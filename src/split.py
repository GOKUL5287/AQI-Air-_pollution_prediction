import numpy as np
import pandas as pd

TEST_QUANTILE = 0.8
GAP_H = 48
LOCKDOWN_START = pd.Timestamp("2020-03-25")


def get_test_start(df: pd.DataFrame, time_col: str = "Datetime",
                   q: float = TEST_QUANTILE) -> pd.Timestamp:
    """80th percentile of the UNIQUE timestamps (an actual timestamp, no interpolation)."""
    ts = np.sort(df[time_col].unique())
    return pd.Timestamp(ts[int(q * (len(ts) - 1))])


def add_split(df: pd.DataFrame):
    """Add `split` (train/gap/test) and `is_lockdown`. Returns (df, test_start)."""
    out = df.copy()
    test_start = get_test_start(out)
    gap_start = test_start - pd.Timedelta(hours=GAP_H)
    t = out["Datetime"]
    out["split"] = np.select([t < gap_start, t < test_start], ["train", "gap"], default="test")
    out["is_lockdown"] = t >= LOCKDOWN_START
    return out, test_start


def split_report(df: pd.DataFrame, test_start: pd.Timestamp) -> None:
    """Print counts and date ranges per split, test_start, and lockdown share of test."""
    gap_start = test_start - pd.Timedelta(hours=GAP_H)
    print("test_start:", test_start, "| gap_start:", gap_start)
    for name in ["train", "gap", "test"]:
        p = df[df["split"] == name]
        print(f"{name:5s} rows={len(p):>10,}   {p['Datetime'].min()} -> {p['Datetime'].max()}")

    tr, ga, te = (df[df["split"] == s]["Datetime"] for s in ["train", "gap", "test"])
    assert tr.max() < ga.min() and ga.max() < te.min(), "splits overlap in time"

    test = df[df["split"] == "test"]
    n_lock = int(test["is_lockdown"].sum())
    print(f"lockdown share of test rows: {n_lock / len(test) * 100:.1f}%  ({n_lock:,} of {len(test):,})")