"""LSTM forecaster over 48-hour station windows of the baseline feature set."""

import copy
import time

import numpy as np
import pandas as pd
import torch
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import BatchSampler, DataLoader, Dataset, RandomSampler, SequentialSampler

from src.baselines import HORIZONS, _feature_columns

WINDOW = 48
HIDDEN = 64
DROPOUT = 0.2
BATCH = 1024
SEED = 42
PATIENCE = 3
MAX_EPOCHS = 50
VAL_FRACTION = 0.1
# Batches are gathered from one in-memory array, so worker processes would only add IPC on CPU.
NUM_WORKERS = 0
TARGETS = [f"Target_AQI_{h}h" for h in HORIZONS]


def make_windows(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Sort df and return it with the last-row index of every gap-free 48h station window."""
    df = df.sort_values(["StationId", "Datetime"]).reset_index(drop=True)
    start = np.arange(len(df)) - (WINDOW - 1)
    first = np.clip(start, 0, None)
    station = df["StationId"].to_numpy()
    t = df["Datetime"].to_numpy()
    ok = (start >= 0) & (station[first] == station)
    ok &= (t - t[first]) == np.timedelta64(WINDOW - 1, "h")
    return df, np.flatnonzero(ok)


def split_windows(df: pd.DataFrame, ends: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Train windows end on a train row with a target; test windows end on a test row."""
    split = df["split"].to_numpy()[ends]
    has_target = df[TARGETS].notna().any(axis=1).to_numpy()[ends]
    return ends[(split == "train") & has_target], ends[split == "test"]


class LSTMNet(nn.Module):
    def __init__(self, n_features: int):
        super().__init__()
        self.lstm = nn.LSTM(n_features, HIDDEN, batch_first=True)
        self.dropout = nn.Dropout(DROPOUT)
        self.head = nn.Linear(HIDDEN, len(HORIZONS))

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.head(self.dropout(out[:, -1]))


class _Windows(Dataset):
    def __init__(self, x, y, ends):
        self.x, self.y, self.ends = x, y, ends

    def __len__(self):
        return len(self.ends)

    def __getitem__(self, batch):
        last = self.ends[batch]
        rows = last[:, None] + np.arange(-WINDOW + 1, 1)
        return torch.from_numpy(self.x[rows]), torch.from_numpy(self.y[last])


def _loader(x, y, ends, generator=None):
    sampler = RandomSampler(ends, generator=generator) if generator else SequentialSampler(ends)
    return DataLoader(
        _Windows(x, y, ends),
        sampler=BatchSampler(sampler, BATCH, drop_last=False),
        batch_size=None,
        num_workers=NUM_WORKERS,
    )


def _masked_mae(pred, y):
    mask = ~torch.isnan(y)
    return (pred[mask] - y[mask]).abs().mean()


@torch.no_grad()
def _predict(model, x, y, ends):
    model.eval()
    return np.concatenate([model(xb).numpy() for xb, _ in _loader(x, y, ends)])


def run_lstm(df: pd.DataFrame, max_epochs: int = MAX_EPOCHS, seed: int = SEED) -> pd.DataFrame:
    """Fit on train windows (last 10% by time for early stopping); predict test windows."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    features = _feature_columns(df)
    df, ends = make_windows(df)
    train_ends, test_ends = split_windows(df, ends)

    times = df["Datetime"].to_numpy()
    train_times = np.sort(np.unique(times[train_ends]))
    val_start = train_times[int((1 - VAL_FRACTION) * (len(train_times) - 1))]
    fit_ends = train_ends[times[train_ends] < val_start]
    val_ends = train_ends[times[train_ends] >= val_start]

    is_train = (df["split"] == "train").to_numpy()
    preprocess = make_pipeline(SimpleImputer(strategy="median"), StandardScaler())
    preprocess.fit(df.loc[is_train, features])
    x = preprocess.transform(df[features]).astype(np.float32)
    y_raw = df[TARGETS].to_numpy(dtype=np.float32)
    y_mean, y_std = np.nanmean(y_raw[is_train], axis=0), np.nanstd(y_raw[is_train], axis=0)
    y = (y_raw - y_mean) / y_std

    model = LSTMNet(x.shape[1])
    optimizer = torch.optim.Adam(model.parameters())
    generator = torch.Generator().manual_seed(seed)
    best, best_state, bad = np.inf, None, 0
    for epoch in range(max_epochs):
        started = time.time()
        model.train()
        losses = []
        for xb, yb in _loader(x, y, fit_ends, generator):
            optimizer.zero_grad()
            loss = _masked_mae(model(xb), yb)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        val = float(_masked_mae(torch.from_numpy(_predict(model, x, y, val_ends)),
                                torch.from_numpy(y[val_ends])))
        print(f"epoch {epoch + 1} train_mae_scaled={np.mean(losses):.4f} val_mae_scaled={val:.4f} "
              f"{time.time() - started:.0f}s", flush=True)
        if val < best:
            best, best_state, best_epoch, bad = val, copy.deepcopy(model.state_dict()), epoch + 1, 0
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    model.load_state_dict(best_state)
    print(f"best epoch {best_epoch} val_mae_scaled={best:.4f} y_std={y_std.round(2).tolist()}", flush=True)

    pred = _predict(model, x, y, test_ends) * y_std + y_mean
    test = df.iloc[test_ends]
    parts = []
    for i, horizon in enumerate(HORIZONS):
        keep = test[TARGETS[i]].notna().to_numpy()
        parts.append(
            pd.DataFrame(
                {
                    "StationId": test["StationId"].to_numpy()[keep],
                    "Datetime": test["Datetime"].to_numpy()[keep],
                    "horizon_h": horizon,
                    "model": "lstm",
                    "y_true": test[TARGETS[i]].to_numpy(dtype=float)[keep],
                    "y_pred": pred[keep, i].astype(float),
                }
            )
        )
    return pd.concat(parts, ignore_index=True)


if __name__ == "__main__":
    import sys

    from src.data_loader import data_dir, load_features

    df = load_features()
    if len(sys.argv) == 1:
        run_lstm(df).to_parquet(data_dir() / "processed" / "predictions_lstm.parquet", index=False)
    for seed in map(int, sys.argv[1:]):
        print(f"seed {seed}", flush=True)
        run_lstm(df, seed=seed).to_parquet(
            data_dir() / "processed" / f"predictions_lstm_seed{seed}.parquet", index=False
        )
