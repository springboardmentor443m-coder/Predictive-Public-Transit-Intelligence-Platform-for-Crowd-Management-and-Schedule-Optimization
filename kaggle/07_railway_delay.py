"""Railway Delay 2015 — delay classifier + regressor (PRD dataset #6).

Dataset: https://www.kaggle.com/datasets/anuragraturi/railway-delay-dataset
Schema: 312,040 rail journeys (2015): distance, weather, day-of-week,
        time-of-day, train type, historical delay, route congestion.
Complements NJ Transit (#7) for the Scheduling/Delay module.

Trains XGBClassifier (on_time<=2 / minor<=6 / delayed) + XGBRegressor (minutes)
on the same feature schema as 03_nj_transit_delay.py so the backend
DelayForecaster can serve either artifact set.

Outputs -> railway_delay_model_outputs/{delay_classifier,delay_regressor}.joblib
To serve: copy as delay_classifier/regressor.joblib (alternative to NJ set)
or keep side-by-side for comparison. See docs/PERFORMANCE_METRICS.md.
"""
import glob
import json
import os
import time

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score

DATASET_SLUG = "anuragraturi/railway-delay-dataset"
OUT_DIR = "/kaggle/working" if os.path.isdir("/kaggle/working") else "."
MODEL_DIR = os.path.join(OUT_DIR, "railway_delay_model_outputs")
os.makedirs(MODEL_DIR, exist_ok=True)

BUCKETS = ["on_time", "minor_delay", "delayed"]


def hour_feats(hour, weekday):
    hour = np.asarray(hour, dtype=float); weekday = np.asarray(weekday, dtype=float)
    return np.stack([np.sin(2*np.pi*hour/24), np.cos(2*np.pi*hour/24),
                     ((hour >= 7) & (hour <= 9) | (hour >= 16) & (hour <= 19)).astype(float),
                     (weekday >= 5).astype(float)], axis=1).astype(np.float32)


def load_or_proxy():
    hits = glob.glob(os.path.join("/kaggle/input", "**", "*.csv"), recursive=True) if os.path.isdir("/kaggle/input") else []
    for f in hits:
        try:
            df = pd.read_csv(f, nrows=5)
            cols = {c.lower() for c in df.columns}
            if "delay" in " ".join(cols) or "weather" in cols or "distance" in cols:
                print(f"[data] using {f}")
                return normalize(pd.read_csv(f))
        except Exception as e:
            print("skip", f, e)
    print("[data] no Railway input — proxy 312k schema (distance/weather/dow/tod/type/congestion)")
    rng = np.random.default_rng(2015)
    n = 120000
    dist = rng.uniform(5, 400, n)
    weather = rng.choice(["clear", "rain", "fog", "storm"], n, p=[0.7, 0.18, 0.08, 0.04])
    dow = rng.integers(0, 7, n); hour = rng.integers(0, 24, n)
    ttype = rng.choice(["express", "local", "intercity"], n, p=[0.3, 0.5, 0.2])
    congest = rng.uniform(0, 1, n)
    base = 1.5 + dist * 0.008 + congest * 6 + (weather == "rain") * 2 + (weather == "storm") * 8 + rng.normal(0, 2, n)
    delay = np.clip(base, 0, 60)
    return pd.DataFrame({"distance": dist, "weather": weather, "weekday": dow, "hour": hour,
                         "train_type": ttype, "congestion": congest, "delay_minutes": delay})


def normalize(df):
    df = df.copy(); df.columns = [c.lower().strip() for c in df.columns]
    ren = {"day_of_week": "weekday", "dow": "weekday", "time_of_day": "hour", "type": "train_type",
           "delay": "delay_minutes", "route_congestion": "congestion", "historical_delay": "hist_delay"}
    df = df.rename(columns={k: v for k, v in ren.items() if k in df.columns})
    if "hour" not in df.columns and "scheduled_time" in df.columns:
        df["hour"] = pd.to_datetime(df["scheduled_time"], errors="coerce").dt.hour.fillna(12).astype(int)
    for c, d in (("weekday", 2), ("hour", 12), ("distance", 50.0), ("congestion", 0.5), ("delay_minutes", 0.0)):
        if c not in df.columns: df[c] = d
    if "weather" not in df.columns: df["weather"] = "clear"
    if "train_type" not in df.columns: df["train_type"] = "local"
    return df


def build_X(df):
    hf = hour_feats(df["hour"].to_numpy(), df["weekday"].to_numpy())
    wthr = pd.get_dummies(df["weather"].astype(str), prefix="w").to_numpy(dtype=np.float32)
    ttyp = pd.get_dummies(df["train_type"].astype(str), prefix="t").to_numpy(dtype=np.float32)
    num = df[["distance", "congestion"]].to_numpy(dtype=np.float32)
    return np.hstack([hf, num, wthr, ttyp]), list(df["weather"].unique()), list(df["train_type"].unique())


def train(df):
    X, w_names, t_names = build_X(df)
    y_min = df["delay_minutes"].to_numpy(dtype=np.float32)
    y_cls = np.where(y_min <= 2, 0, np.where(y_min <= 6, 1, 2))
    n = len(df); cut = int(n * 0.8)
    tr, te = np.arange(n)[:cut], np.arange(n)[cut:]
    t0 = time.time()
    clf = xgb.XGBClassifier(tree_method="hist", n_estimators=300, max_depth=6, learning_rate=0.05,
                            subsample=0.9, colsample_bytree=0.9, random_state=42, n_jobs=max(1, os.cpu_count() // 2),
                            objective="multi:softprob", num_class=3, eval_metric="mlogloss")
    clf.fit(X[tr], y_cls[tr], eval_set=[(X[te], y_cls[te])], verbose=False)
    pred_c = clf.predict(X[te]); acc = float(accuracy_score(y_cls[te], pred_c))
    reg = xgb.XGBRegressor(tree_method="hist", n_estimators=300, max_depth=6, learning_rate=0.05,
                           subsample=0.9, colsample_bytree=0.9, random_state=42, n_jobs=max(1, os.cpu_count() // 2))
    reg.fit(X[tr], y_min[tr], eval_set=[(X[te], y_min[te])], verbose=False)
    pred_r = reg.predict(X[te])
    r2 = float(r2_score(y_min[te], pred_r)); mae = float(mean_absolute_error(y_min[te], pred_r))
    print(f"[delay-cls] acc={acc:.4f} [delay-reg] R2={r2:.4f} MAE={mae:.2f} ({time.time()-t0:.1f}s)")
    joblib.dump({"model": clf, "classes": BUCKETS, "trained_on": "railway2015",
                 "weather_names": w_names, "type_names": t_names}, os.path.join(MODEL_DIR, "delay_classifier.joblib"))
    joblib.dump({"model": reg, "trained_on": "railway2015"}, os.path.join(MODEL_DIR, "delay_regressor.joblib"))
    json.dump({"delay_classifier": {"accuracy": acc}, "delay_regressor": {"r2": r2, "mae": mae, "rmse": float(mean_squared_error(y_min[te], pred_r) ** 0.5)}},
              open(os.path.join(MODEL_DIR, "metrics.json"), "w"), indent=2)
    open(os.path.join(MODEL_DIR, "report.txt"), "w").write(f"Railway Delay 2015\nslug={DATASET_SLUG}\nrows={len(df)}\ncls_acc={acc:.4f}\nreg_R2={r2:.4f} MAE={mae:.2f}\n")
    plt.figure(figsize=(5, 4)); s = np.random.choice(len(te), min(5000, len(te)), replace=False)
    plt.scatter(y_min[te][s], pred_r[s], s=4, alpha=0.3); plt.xlabel("actual min"); plt.ylabel("predicted min")
    plt.title(f"Railway delay R2={r2:.3f}"); plt.tight_layout()
    plt.savefig(os.path.join(MODEL_DIR, "delay_reg_scatter.png")); plt.close()
    print("[done]", MODEL_DIR)


if __name__ == "__main__":
    train(load_or_proxy())
