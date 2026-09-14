"""Feature engineering + sklearn crowd forecasting model."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

FEATURES = ["hour", "dow", "month", "is_weekend", "is_peak", "lag_1", "lag_24", "roll_24"]


def add_features(g: pd.DataFrame) -> pd.DataFrame:
    g = g.copy().sort_values("timestamp")
    g["hour"] = g["timestamp"].dt.hour
    g["dow"] = g["timestamp"].dt.dayofweek
    g["month"] = g["timestamp"].dt.month
    g["is_weekend"] = (g["dow"] >= 5).astype(int)
    g["is_peak"] = g["hour"].isin([7, 8, 9, 17, 18, 19]).astype(int)
    g["lag_1"] = g["entries"].shift(1).fillna(g["entries"].mean())
    g["lag_24"] = g["entries"].shift(24).fillna(g["entries"].mean())
    g["roll_24"] = g["entries"].shift(1).rolling(24, min_periods=1).mean().fillna(g["entries"].mean())
    return g


def train(df: pd.DataFrame, model_path: str | Path) -> dict:
    frames = []
    for _, g in df.groupby("station_code"):
        frames.append(add_features(g))
    full = pd.concat(frames, ignore_index=True)
    # One-hot station? Use per-station mean encoding for simplicity + global model
    station_mean = full.groupby("station_code")["entries"].mean().to_dict()
    full["station_base"] = full["station_code"].map(station_mean)
    feats = FEATURES + ["station_base"]
    X, y = full[feats], full["entries"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
    model = RandomForestRegressor(n_estimators=120, max_depth=14, n_jobs=-1, random_state=42)
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    metrics = {
        "mae": float(mean_absolute_error(yte, pred)),
        "r2": float(r2_score(yte, pred)),
        "mean_entries": float(y.mean()),
        "n_rows": int(len(full)),
        "n_stations": int(df["station_code"].nunique()),
    }
    # mape-style accuracy proxy
    metrics["accuracy_pct"] = float(max(0.0, 100 * (1 - metrics["mae"] / max(1, metrics["mean_entries"]))))
    bundle = {"model": model, "station_mean": station_mean, "global_mean": float(y.mean()), "features": feats}
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_path)
    return metrics


def load_bundle(model_path: str | Path):
    import os
    if not os.path.exists(model_path):
        return None
    return joblib.load(model_path)


def forecast(df_station: pd.DataFrame, bundle, hours: int = 24) -> pd.DataFrame:
    """Iterative multi-step forecast using lag features."""
    g = add_features(df_station.sort_values("timestamp").copy())
    model = bundle["model"]
    feats = bundle["features"]
    last_ts = g["timestamp"].max()
    hist_entries = list(g["entries"].values)
    rows = []
    for h in range(1, hours + 1):
        ts = last_ts + pd.Timedelta(hours=h)
        lag_1 = hist_entries[-1]
        lag_24 = hist_entries[-24] if len(hist_entries) >= 24 else float(np.mean(hist_entries))
        roll_24 = float(np.mean(hist_entries[-24:]))
        rec = {
            "hour": ts.hour, "dow": ts.dayofweek, "month": ts.month,
            "is_weekend": int(ts.dayofweek >= 5),
            "is_peak": int(ts.hour in (7, 8, 9, 17, 18, 19)),
            "lag_1": lag_1, "lag_24": lag_24, "roll_24": roll_24,
            "station_base": bundle["station_mean"].get(
                df_station["station_code"].iloc[0], bundle["global_mean"]),
        }
        X = pd.DataFrame([rec])[feats]
        pred_entries = float(max(0, model.predict(X)[0]))
        # exits correlated ~0.9 of entries with noise-free estimate
        pred_exits = float(max(0, pred_entries * 0.92))
        rows.append({"timestamp": ts, "predicted_entries": pred_entries,
                     "predicted_exits": pred_exits,
                     "predicted_total": pred_entries + pred_exits})
        hist_entries.append(pred_entries)
    out = pd.DataFrame(rows)
    # Fix is_weekend calc (Timestamp.dayofweek is property)
    return out
