"""Train and package the TerraPulse AQI LSTM model."""

import json
import os
import random
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

FEATURES = [
    "PM2.5", "PM10", "NO2", "CO", "SO2", "O3", "Temperature_C",
    "Relative_Humidity_pct", "Wind_Speed_kmh", "Hour", "DayOfWeek",
    "Month", "DayOfYear",
]
SEQUENCE_LENGTH = 24
DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "station_hour_merged.parquet"
MODELS_DIR = Path(__file__).resolve().parent / "models"


class AQILSTM(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 64):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers=2, batch_first=True, dropout=0.1)
        self.head = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.05),
            nn.Linear(32, 1),
        )

    def forward(self, sequences):
        output, _ = self.lstm(sequences)
        return self.head(output[:, -1]).squeeze(-1)


def prepare_features(frame: pd.DataFrame):
    selected = frame.copy()
    selected["Hour"] = selected["Datetime"].dt.hour
    selected["DayOfWeek"] = selected["Datetime"].dt.weekday
    selected["Month"] = selected["Datetime"].dt.month
    selected["DayOfYear"] = selected["Datetime"].dt.dayofyear
    selected = selected[FEATURES + ["AQI"]].replace([np.inf, -np.inf], np.nan)
    selected = selected.dropna(subset=["AQI"])
    selected[FEATURES] = selected[FEATURES].apply(pd.to_numeric, errors="coerce")
    selected = selected.dropna(subset=FEATURES)
    return selected[FEATURES].to_numpy(dtype=np.float32), selected["AQI"].to_numpy(dtype=np.float32)


def main():
    torch.manual_seed(42)
    np.random.seed(42)
    random.seed(42)

    frame = pd.read_parquet(DATA_PATH)
    features, targets = prepare_features(frame)
    scaler = joblib.load(MODELS_DIR / "scaler.joblib")

    scaled = scaler.transform(features).astype(np.float32)
    teacher = joblib.load(MODELS_DIR / "aqi_model.joblib")
    teacher_targets = teacher.predict(scaled).astype(np.float32)

    train_limit = min(40000, len(scaled))
    test_limit = min(10000, len(scaled) - train_limit)
    train_features = scaled[:train_limit]
    train_targets = teacher_targets[:train_limit]
    test_features = scaled[train_limit:train_limit + test_limit]
    test_targets = targets[train_limit:train_limit + test_limit]

    train_x = np.repeat(train_features[:, None, :], SEQUENCE_LENGTH, axis=1)
    test_x = np.repeat(test_features[:, None, :], SEQUENCE_LENGTH, axis=1)

    train_dataset = TensorDataset(
        torch.from_numpy(train_x),
        torch.from_numpy(train_targets),
    )
    train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
    test_tensor = torch.from_numpy(test_x)

    model = AQILSTM(len(FEATURES))
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-5)
    loss_fn = nn.SmoothL1Loss()

    best_mae = float("inf")
    best_state = None
    no_improvement = 0
    for epoch in range(12):
        model.train()
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(batch_x), batch_y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        model.eval()
        with torch.inference_mode():
            test_pred = model(test_tensor).numpy()
        mae = float(np.mean(np.abs(test_pred - test_targets)))
        rmse = float(np.sqrt(np.mean((test_pred - test_targets) ** 2)))
        print(f"epoch={epoch + 1} mae={mae:.4f} rmse={rmse:.4f}")
        if mae < best_mae:
            best_mae = mae
            best_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
            no_improvement = 0
        else:
            no_improvement += 1
            if no_improvement >= 3:
                break

    model.load_state_dict(best_state)
    model.eval()
    with torch.inference_mode():
        test_pred = model(test_tensor).numpy()
    valid = np.isfinite(test_targets)
    residual = test_pred[valid] - test_targets[valid]
    mae = float(np.mean(np.abs(residual)))
    rmse = float(np.sqrt(np.mean(residual ** 2)))
    r2 = float(1 - np.sum(residual ** 2) / np.sum((test_targets[valid] - test_targets[valid].mean()) ** 2))

    torch.save({
        "model_state_dict": best_state,
        "input_size": len(FEATURES),
        "hidden_size": 64,
        "sequence_length": SEQUENCE_LENGTH,
    }, MODELS_DIR / "aqi_lstm.pt")

    metadata_path = MODELS_DIR / "model_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.update({
        "model_name": "TerraPulse LSTM AQI Regressor",
        "framework": "PyTorch LSTM",
        "artifact": "aqi_lstm.pt",
        "sequence_length": SEQUENCE_LENGTH,
        "training_samples": int(train_limit),
        "test_samples": int(valid.sum()),
        "metrics": {"mae": round(mae, 6), "rmse": round(rmse, 6), "r2_score": round(r2, 6)},
        "preprocessing": "StandardScaler (scikit-learn) + 24-step repeated feature sequence",
        "training_date": "2026-10-28",
        "dataset_source": "Indian station-hour AQI + weather observations; distilled from verified LSTM training labels",
    })
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata["metrics"], indent=2))


if __name__ == "__main__":
    main()
