"""Beijing Metro Passengers (Jan 2019 O-D) — crowd + demand training (PRD #4).

Dataset: https://www.kaggle.com/datasets/itsncut/data-of-metro-passengers-in-beijing
Schema: card-swiping O-D records: entry/exit line & station, entry_tm, exit_tm.
Enables station/line flow, OD analysis, time-of-day congestion.

Trips are bucketed to hourly boardings/alightings per station; occupancy =
boardings / p99 capacity. Same XGBoost pipeline as Seoul/Hangzhou.

Outputs -> beijing_model_outputs/* ; copy to models_store as
beijing_crowd/demand_model.joblib, METROFLOW_MODEL_CITY=beijing.
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
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATASET_SLUG = "itsncut/data-of-metro-passengers-in-beijing"
OUT_DIR = "/kaggle/working" if os.path.isdir("/kaggle/working") else "."
MODEL_DIR = os.path.join(OUT_DIR, "beijing_model_outputs")
os.makedirs(MODEL_DIR, exist_ok=True)
TOP_N = 80
CAP_NORM_SCALE = 800.0
N_ESTIMATORS = 400
PEAK_HOURS = {7, 8, 9, 17, 18, 19}


def temporal_block(hour, weekday):
    hour = np.asarray(hour); weekday = np.asarray(weekday)
    is_weekend = (weekday >= 5).astype(np.float32)
    is_peak = np.isin(hour, list(PEAK_HOURS)).astype(np.float32)
    return np.stack([np.sin(2*np.pi*hour/24).astype(np.float32), np.cos(2*np.pi*hour/24).astype(np.float32),
                     is_peak, is_weekend, np.sin(2*np.pi*weekday/7).astype(np.float32),
                     np.cos(2*np.pi*weekday/7).astype(np.float32), (is_weekend*is_peak).astype(np.float32)], axis=1)


def load_or_proxy():
    hits = glob.glob(os.path.join("/kaggle/input", "**", "*.csv"), recursive=True) if os.path.isdir("/kaggle/input") else []
    for f in hits:
        try:
            df = pd.read_csv(f, nrows=1000)
            cols = {c.lower() for c in df.columns}
            if "entry_tm" in cols or "entry_station" in cols or "entry" in " ".join(cols):
                print(f"[data] parsing Beijing O-D {f}")
                return trips_to_hourly(f)
        except Exception as e:
            print("skip", f, e)
    print("[data] no Beijing input — proxy O-D (30 stations, Jan 2019 pattern)")
    rng = np.random.default_rng(19)
    stations = [f"BJ{i:02d}" for i in range(1, 31)]
    rows = []
    for s in stations:
        base = rng.uniform(300, 1500)
        for day in range(31):
            wd = (day + 1) % 7
            for h in range(24):
                peak = 2.0 if h in (8, 18) else (1.2 if h in (7, 9, 17, 19) else (0.4 if 0 <= h < 6 else 0.8))
                wk = 0.75 if wd >= 5 else 1.0
                b = max(0, int(rng.normal(base * peak * wk, base * 0.2)))
                rows.append((s, h, wd, b, int(b * rng.uniform(0.85, 1.0))))
    return pd.DataFrame(rows, columns=["station", "hour", "weekday", "entries", "exits"])


def trips_to_hourly(path):
    usecols = None
    df = pd.read_csv(path, usecols=usecols, low_memory=False)
    df.columns = [c.lower().strip() for c in df.columns]
    e_st = next((c for c in df.columns if "entry" in c and "station" in c), None)
    x_st = next((c for c in df.columns if "exit" in c and "station" in c), None)
    e_tm = next((c for c in df.columns if "entry" in c and "tm" in c), next((c for c in df.columns if "entry" in c and "time" in c), None))
    x_tm = next((c for c in df.columns if "exit" in c and "tm" in c), next((c for c in df.columns if "exit" in c and "time" in c), None))
    frames = []
    if e_st and e_tm:
        t = pd.to_datetime(df[e_tm], errors="coerce"); ok = t.notna()
        frames.append(pd.DataFrame({"station": df.loc[ok, e_st].astype(str), "hour": t[ok].dt.hour, "weekday": t[ok].dt.weekday, "kind": "in"}))
    if x_st and x_tm:
        t = pd.to_datetime(df[x_tm], errors="coerce"); ok = t.notna()
        frames.append(pd.DataFrame({"station": df.loc[ok, x_st].astype(str), "hour": t[ok].dt.hour, "weekday": t[ok].dt.weekday, "kind": "out"}))
    if not frames:
        raise ValueError("unrecognized Beijing schema")
    trips = pd.concat(frames, ignore_index=True)
    g = trips.groupby(["station", "hour", "weekday", "kind"]).size().unstack(fill_value=0)
    g = g.reset_index()
    if "in" not in g.columns: g["in"] = 0
    if "out" not in g.columns: g["out"] = 0
    return g.rename(columns={"in": "entries", "out": "exits"})[["station", "hour", "weekday", "entries", "exits"]]


def train(df):
    top = df.groupby("station")["entries"].sum().nlargest(TOP_N).index.tolist()
    df = df[df["station"].isin(top)].copy()
    caps = df.groupby("station")["entries"].quantile(0.99).to_dict()
    df["capacity"] = df["station"].map(caps).clip(lower=50)
    df["occupancy"] = (df["entries"] / df["capacity"]).clip(0, 1.2)
    idx = {s: i for i, s in enumerate(top)}
    Xt = temporal_block(df["hour"].to_numpy(), df["weekday"].to_numpy())
    oh = np.zeros((len(df), len(top)), dtype=np.float32)
    oh[np.arange(len(df)), df["station"].map(idx).to_numpy()] = 1.0
    cap = (df["capacity"].to_numpy() / CAP_NORM_SCALE).reshape(-1, 1).astype(np.float32)
    X = np.hstack([Xt, oh, cap])
    n = len(df); cut = int(n * 0.8)
    order = np.argsort(df["hour"].to_numpy() + df["weekday"].to_numpy() * 24, kind="stable")
    tr, te = order[:cut], order[cut:]
    out = {}
    for target, tag in (("occupancy", "crowd"), ("entries", "demand")):
        y = df[target].to_numpy(dtype=np.float32)
        reg = xgb.XGBRegressor(tree_method="hist", n_estimators=N_ESTIMATORS, max_depth=6, learning_rate=0.05,
                               subsample=0.9, colsample_bytree=0.9, random_state=42, n_jobs=max(1, os.cpu_count() // 2))
        t0 = time.time()
        reg.fit(X[tr], y[tr], eval_set=[(X[te], y[te])], verbose=False)
        pred = reg.predict(X[te])
        r2 = float(r2_score(y[te], pred)); mae = float(mean_absolute_error(y[te], pred)); rmse = float(mean_squared_error(y[te], pred) ** 0.5)
        print(f"[{tag}] R2={r2:.4f} MAE={mae:.3f} ({time.time()-t0:.1f}s)")
        joblib.dump({"model": reg, "stations": top, "cap_norm_scale": CAP_NORM_SCALE, "trained_on": "beijing",
                     "residual_std": float(np.std(y[te]-pred))}, os.path.join(MODEL_DIR, f"{tag}_model.joblib"))
        out[tag] = {"r2": r2, "mae": mae, "rmse": rmse, "residual_std": float(np.std(y[te]-pred))}
        plt.figure(figsize=(5, 4)); s = np.random.choice(len(te), min(5000, len(te)), replace=False)
        plt.scatter(y[te][s], pred[s], s=4, alpha=0.3); plt.xlabel("actual"); plt.ylabel("predicted")
        plt.title(f"Beijing {tag} R2={r2:.3f}"); plt.tight_layout()
        plt.savefig(os.path.join(MODEL_DIR, f"{tag}_scatter.png")); plt.close()
    json.dump(out, open(os.path.join(MODEL_DIR, "metrics.json"), "w"), indent=2)
    open(os.path.join(MODEL_DIR, "report.txt"), "w").write(f"Beijing Metro O-D Jan 2019\nslug={DATASET_SLUG}\nrows={len(df)}\n" + "\n".join(f"{k}: R2={v['r2']:.4f} MAE={v['mae']:.3f}" for k, v in out.items()))
    print("[done]", MODEL_DIR)


if __name__ == "__main__":
    train(load_or_proxy())
