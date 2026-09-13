import glob
import json
import multiprocessing as mp
import os
import subprocess
import time
import zipfile

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    auc,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    precision_recall_curve,
    r2_score,
    roc_auc_score,
    roc_curve,
)

DATASET_SLUG = "kimjmin/seoul-metro-usage"
DATASET_NAME = "seoul"
OUT_DIR = "/kaggle/working" if os.path.isdir("/kaggle/working") else "."
MODEL_DIR = os.path.join(OUT_DIR, DATASET_NAME + "_outputs")
os.makedirs(MODEL_DIR, exist_ok=True)

RANDOM_STATE = 42
TEST_FRACTION = 0.20
MAX_ROWS = 4_000_000
PEAK_HOURS = {7, 8, 9, 16, 17, 18}
HOURS_PER_DAY = 24
TOP_N_STATIONS = 100
CAP_NORM_SCALE = 700.0
N_ESTIMATORS = 400
EARLY_STOP = 25
N_THREADS = max(1, os.cpu_count() // 2)

XGB_MAJOR = int(xgb.__version__.split(".")[0])


def xgb_reg_params(extra=None):
    params = {
        "tree_method": "hist",
        "n_estimators": N_ESTIMATORS,
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "min_child_weight": 2,
        "reg_lambda": 1.0,
        "n_jobs": N_THREADS,
        "random_state": RANDOM_STATE,
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
    }
    if XGB_MAJOR >= 2:
        params["device"] = "cuda"
    else:
        params["tree_method"] = "gpu_hist"
    if extra:
        params.update(extra)
    return params


def print_gpus():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.free", "--format=csv"],
            capture_output=True, text=True, check=True,
        ).stdout
        print(out)
    except Exception as e:
        print("[gpu] nvidia-smi unavailable:", e)


def search_input_files(patterns, root="/kaggle/input", slug=None):
    base = root
    if slug:
        sdir = os.path.join(root, slug.split("/")[-1])
        if os.path.isdir(sdir):
            base = sdir
    hits = []
    if os.path.isdir(base):
        for pat in patterns:
            hits += glob.glob(os.path.join(base, "**", pat), recursive=True)
    return sorted(set(hits))


def kagglehub_download(slug):
    try:
        import kagglehub
        path = kagglehub.dataset_download(slug)
        print("[data] kagglehub downloaded", slug, "->", path)
        return path
    except Exception as e:
        print("[data] kagglehub failed:", e)
        return None


def temporal_block(hour, weekday):
    is_weekend = (weekday >= 5).astype(np.float32)
    is_peak = np.isin(hour, list(PEAK_HOURS)).astype(np.float32)
    h_sin = np.sin(2 * np.pi * hour / HOURS_PER_DAY).astype(np.float32)
    h_cos = np.cos(2 * np.pi * hour / HOURS_PER_DAY).astype(np.float32)
    d_sin = np.sin(2 * np.pi * weekday / 7).astype(np.float32)
    d_cos = np.cos(2 * np.pi * weekday / 7).astype(np.float32)
    return np.stack([h_sin, h_cos, is_peak, is_weekend, d_sin, d_cos, (is_weekend * is_peak)], axis=1)


def build_fmat(df, station_index):
    blocks = [temporal_block(df["hour"].to_numpy(), df["weekday"].to_numpy())]
    n = len(df)
    n_stations = len(station_index)
    oh = np.zeros((n, n_stations), dtype=np.float32)
    codes = df["station_ix"].to_numpy()
    valid = codes >= 0
    oh[valid, codes[valid]] = 1.0
    cap = np.clip(df["capacity"].to_numpy() / CAP_NORM_SCALE, 0.0, 1.5).astype(np.float32).reshape(-1, 1)
    blocks.append(oh)
    blocks.append(cap)
    return np.hstack(blocks)


def congestion_bucket(pct):
    if pct >= 0.90:
        return "critical"
    if pct >= 0.75:
        return "high"
    if pct >= 0.55:
        return "medium"
    return "low"


BUCKET_ORDER = ["low", "medium", "high", "critical"]


def plot_confusion(y_true, y_pred, classes, title, path, normalize=True):
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    disp = cm.astype("float") / cm.sum(axis=1, keepdims=True) if normalize else cm
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.imshow(disp, cmap="Blues")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = f"{disp[i, j]:.2f}" if normalize else str(int(cm[i, j]))
            color = "white" if disp[i, j] > 0.5 else "black"
            ax.text(j, i, val, ha="center", va="center", color=color, fontsize=9)
    ax.set_xticks(range(len(classes)), classes, rotation=45, ha="right")
    ax.set_yticks(range(len(classes)), classes)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return cm


def plot_scatter_resids(y_true, y_pred, title, prefix, out_dir, label_units, sample=200000):
    ix = np.random.RandomState(RANDOM_STATE).choice(len(y_true), size=min(sample, len(y_true)), replace=False)
    yt, yp = y_true[ix], y_pred[ix]

    fig, ax = plt.subplots(figsize=(6, 5.5))
    ax.scatter(yt, yp, s=6, alpha=0.12, rasterized=True)
    lo = min(yt.min(), yp.min()); hi = max(yt.max(), yp.max())
    ax.plot([lo, hi], [lo, hi], "r--", lw=1)
    ax.set_xlabel("Actual " + label_units)
    ax.set_ylabel("Predicted " + label_units)
    ax.set_title(title + " - actual vs predicted")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, prefix + "_scatter.png"), dpi=130)
    plt.close(fig)

    res = yt - yp
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.hist(res, bins=80, density=True, alpha=0.7, color="steelblue")
    ax.axvline(0, color="red", ls="--", lw=1)
    ax.set_xlabel("Residual (actual - predicted)")
    ax.set_title(title + " - residuals")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, prefix + "_residuals.png"), dpi=130)
    plt.close(fig)


def plot_importance(model, feature_names, title, path, top=25):
    imp = np.asarray(model.feature_importances_, dtype=float)
    order = np.argsort(imp)[::-1][:top]
    names = [feature_names[i] for i in order]
    vals = imp[order]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(range(len(vals))[::-1], vals, color="steelblue")
    ax.set_yticks(range(len(vals))[::-1], names, fontsize=7)
    ax.set_xlabel("Feature importance")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return dict(zip(names, vals.tolist()))


def plot_profile24(actual_by_hour, pred_by_hour, station_label, title, path):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(range(24), actual_by_hour, "o-", label="actual", markersize=4)
    ax.plot(range(24), pred_by_hour, "s--", label="predicted", markersize=4)
    ax.set_xlabel("Hour"); ax.set_ylabel("Passengers")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fit_predict(X, y, params, eval_set):
    if XGB_MAJOR >= 3:
        params = dict(params)
        params["early_stopping_rounds"] = EARLY_STOP
        model = xgb.XGBRegressor(**params)
    else:
        model = xgb.XGBRegressor(**params)
    model.fit(X, y, eval_set=[eval_set], verbose=False)
    return model


def _train_runner(gpu_id, tag, fn, args, queue):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    t0 = time.time()
    try:
        result = fn(*args)
        result["tag"] = tag
        result["gpu"] = gpu_id
        result["elapsed_sec"] = round(time.time() - t0, 1)
        print(f"[{tag}] GPU{gpu_id} finished in {result['elapsed_sec']}s")
    except Exception as e:
        result = {"tag": tag, "gpu": gpu_id, "error": repr(e)}
        print(f"[{tag}] GPU{gpu_id} FAILED: {e}")
    queue.put((tag, result))


def run_on_two_gpus(jobs):
    ctx = mp.get_context("fork") if "fork" in mp.get_all_start_methods() else mp.get_context("spawn")
    queue = ctx.Queue()
    procs = []
    for gpu_id, j in enumerate(jobs):
        tag, fn, args = j
        p = ctx.Process(target=_train_runner, args=(gpu_id, tag, fn, args, queue))
        p.start()
        procs.append(p)
    results = {}
    for _ in procs:
        tag, payload = queue.get()
        results[tag] = payload
    for p in procs:
        p.join()
        if isinstance(p.exitcode, int) and p.exitcode != 0:
            results.setdefault(str(p.pid), {"error": f"exitcode {p.exitcode}"})
    return results


def _save_artifact(path, artifact):
    joblib.dump(artifact, path)
    print("[save]", path)


def load_dataset():
    root = None
    files = search_input_files(["seoul-metro-*.logs.csv"])
    if not files:
        root = kagglehub_download(DATASET_SLUG)
        files = search_input_files(["seoul-metro-*.logs.csv"], root=root) if root else []
    if not files:
        raise RuntimeError("Seoul log CSVs not found. Add the dataset via 'Add Data' or check the slug.")

    frames = []
    for f in files:
        df = pd.read_csv(f)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        if df["timestamp"].dt.tz is not None:
            df["timestamp"] = df["timestamp"].dt.tz_localize(None)
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df = df.rename(columns={"people_in": "entries", "people_out": "exits"})
    df["station_code"] = df["station_code"].astype(str)
    df["hour"] = df["timestamp"].dt.hour
    df["weekday"] = df["timestamp"].dt.weekday
    df = df.dropna(subset=["timestamp", "entries", "exits"])

    info = search_input_files(["seoul-metro-station-info.csv"])
    if info:
        meta = pd.read_csv(info[0])
        if "station.code" in meta.columns:
            meta["station_code"] = meta["station.code"].astype(str)
            meta["station_name"] = meta.get("station.name")
            meta["line"] = meta.get("line.name")
            df = df.merge(meta[["station_code", "station_name", "line"]], on="station_code", how="left")

    print("[data] seoul rows:", len(df), "stations:", df["station_code"].nunique())
    return df


def derive_targets(df):
    cap = df.groupby("station_code")["entries"].transform(lambda s: max(1, int(np.percentile(s.values, 99))))
    df["capacity"] = cap
    df["occupancy"] = df["entries"].astype(int)
    df["occupancy_pct"] = np.clip(df["entries"] / cap, 0.02, 1.15)
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)
    df["is_peak"] = df["hour"].isin(PEAK_HOURS).astype(int)
    df["congestion_level"] = df["occupancy_pct"].map(congestion_bucket)
    return df


def prepare():
    df = load_dataset()
    df = derive_targets(df)
    df = df.sort_values("timestamp").reset_index(drop=True)
    if len(df) > MAX_ROWS:
        df = df.sample(n=MAX_ROWS, random_state=RANDOM_STATE).sort_values("timestamp").reset_index(drop=True)

    rank = df.groupby("station_code")["entries"].sum().sort_values(ascending=False).head(TOP_N_STATIONS)
    stations = rank.index.tolist()
    ix_map = {s: i for i, s in enumerate(stations)}
    df["station_ix"] = df["station_code"].map(ix_map).fillna(-1).astype(int)

    split_at = int(len(df) * (1 - TEST_FRACTION))
    train_ix = np.arange(0, split_at, dtype=int)
    test_ix = np.arange(split_at, len(df), dtype=int)

    X = build_fmat(df, stations)
    y_crowd = (df["occupancy"] / df["capacity"]).to_numpy(dtype=np.float32)
    y_demand = df["entries"].to_numpy(dtype=np.float32)
    feature_names = (["hour_sin", "hour_cos", "is_peak", "is_weekend", "dow_sin", "dow_cos", "weekend_peak"]
                     + [f"station_{s}" for s in stations] + ["capacity_norm"])
    df_ctx = df.reset_index(drop=True)

    return {
        "df": df_ctx, "X": X, "y_crowd": y_crowd, "y_demand": y_demand,
        "stations": stations, "feature_names": feature_names,
        "train_ix": train_ix, "test_ix": test_ix, "out_dir": MODEL_DIR,
    }


def eval_regression(y_true, y_pred, prefix, title, label_units="units"):
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    residual_std = float(np.std(y_true - y_pred))
    plot_scatter_resids(y_true, y_pred, title, prefix, MODEL_DIR, label_units)
    print(f"[{prefix}] MAE={mae:.4f} RMSE={rmse:.4f} R2={r2:.4f} residual_std={residual_std:.4f}")
    return {"mae": mae, "rmse": rmse, "r2": r2, "residual_std": residual_std}


def _train_crowd(ctx, y_crowd, *_):
    df, X = ctx["df"], ctx["X"]
    tr, te = ctx["train_ix"], ctx["test_ix"]
    X_tr, X_te = X[tr], X[te]
    y_tr = y_crowd[tr]
    y_te = y_crowd[te]

    model = fit_predict(X_tr, y_tr, xgb_reg_params(), (X_te, y_te))
    preds = model.predict(X_te)

    metrics = eval_regression(y_te, preds, "crowd", "Crowd occupancy fraction", "occupancy fraction")
    metrics["feature_importance"] = plot_importance(
        model, ctx["feature_names"], "Crowd model - feature importance",
        os.path.join(MODEL_DIR, "crowd_importance.png"))
    best_iter = getattr(model, "best_iteration", None)
    metrics["best_iteration"] = int(best_iter) if best_iter is not None else None

    actual_b = np.array([congestion_bucket(v) for v in y_te])
    pred_b = np.array([congestion_bucket(v) for v in np.clip(preds, 0.0, 1.2)])
    cm = plot_confusion(actual_b, pred_b, BUCKET_ORDER, "Crowd congestion (actual vs predicted)",
                        os.path.join(MODEL_DIR, "crowd_confusion.png"))
    metrics["congestion_confusion_matrix"] = cm.tolist()

    pk = df["is_peak"].to_numpy()[te] == 1
    if pk.any():
        metrics["peak_hour_mae"] = float(mean_absolute_error(y_te[pk], preds[pk]))
        metrics["peak_share_mae"] = round(metrics["peak_hour_mae"] / max(1e-9, metrics["mae"]), 3)

    _save_artifact(os.path.join(MODEL_DIR, "crowd_model.joblib"), {
        "model": model, "residual_std": metrics["residual_std"],
        "stations": ctx["stations"], "feature_names": ctx["feature_names"],
        "cap_norm_scale": CAP_NORM_SCALE, "trained_on": DATASET_NAME,
    })
    return metrics


def _train_demand(ctx, y_demand, *_):
    df, X = ctx["df"], ctx["X"]
    tr, te = ctx["train_ix"], ctx["test_ix"]

    model = fit_predict(X[tr], y_demand[tr], xgb_reg_params(), (X[te], y_demand[te]))
    preds = model.predict(X[te])

    metrics = eval_regression(y_demand[te], preds, "demand", "Hourly demand (entries)", "passengers")
    metrics["feature_importance"] = plot_importance(
        model, ctx["feature_names"], "Demand model - feature importance",
        os.path.join(MODEL_DIR, "demand_importance.png"))
    best_iter = getattr(model, "best_iteration", None)
    metrics["best_iteration"] = int(best_iter) if best_iter is not None else None

    dft = df.iloc[te].copy()
    dft["pred"] = np.clip(preds, 0, None)
    for st in ctx["stations"][:3]:
        sub = dft[dft["station_code"] == st].sort_values("timestamp")
        if len(sub) >= 24:
            hours = sub["hour"].to_numpy()
            y = sub["entries"].to_numpy().astype(float)
            p = sub["pred"].to_numpy().astype(float)
            bins = np.zeros(24); counts = np.zeros(24)
            for h, a, b in zip(hours, y, p):
                bins[h] += a; counts[h] += 1
            a24 = np.where(counts > 0, bins / np.maximum(counts, 1), 0)
            bins = np.zeros(24); counts = np.zeros(24)
            for h, b in zip(hours, p):
                bins[h] += b; counts[h] += 1
            p24 = np.where(counts > 0, bins / np.maximum(counts, 1), 0)
            plot_profile24(a24, p24, st, f"Demand 24h profile - {st}",
                           os.path.join(MODEL_DIR, f"demand_profile_{st}.png"))
    metrics["demand_peak_mae"] = float(mean_absolute_error(
        y_demand[te][df["is_peak"].to_numpy()[te] == 1],
        preds[df["is_peak"].to_numpy()[te] == 1]))

    _save_artifact(os.path.join(MODEL_DIR, "demand_model.joblib"), {
        "model": model, "residual_std": metrics["residual_std"],
        "stations": ctx["stations"], "feature_names": ctx["feature_names"],
        "cap_norm_scale": CAP_NORM_SCALE, "trained_on": DATASET_NAME,
    })
    return metrics


def main():
    print("=" * 72)
    print("MetroFlow | Kaggle training |", DATASET_NAME, "|", DATASET_SLUG)
    print("XGBoost", xgb.__version__, "| threads", N_THREADS)
    print_gpus()
    print("=" * 72)

    ctx = prepare()
    results = run_on_two_gpus([
        ("crowd", _train_crowd, (ctx, ctx["y_crowd"])),
        ("demand", _train_demand, (ctx, ctx["y_demand"])),
    ])

    report_lines = ["MetroFlow training report", DATASET_NAME, DATASET_SLUG, ""]
    for tag, res in sorted(results.items()):
        report_lines.append(f"--- {tag} ---")
        for k, v in res.items():
            if k == "congestion_confusion_matrix":
                report_lines.append("congestion_confusion_matrix: (see PNG)")
                continue
            report_lines.append(f"{k}: {v}")
        report_lines.append("")
    report_lines.append("Confusion matrix (crowd congestion, rows=actual, cols=predicted):")
    cm = results.get("crowd", {}).get("congestion_confusion_matrix")
    if cm:
        report_lines.append("  " + " ".join(f"{BUCKET_ORDER[i]:>9}" for i in range(len(BUCKET_ORDER))))
        for i, row in enumerate(cm):
            report_lines.append(f"{BUCKET_ORDER[i]:>9} " + " ".join(f"{c:9d}" for c in row))
    report_path = os.path.join(MODEL_DIR, "report.txt")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(report_lines))
    with open(os.path.join(MODEL_DIR, "metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, default=str)

    zpath = os.path.join(OUT_DIR, DATASET_NAME + "_model_outputs.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(glob.glob(os.path.join(MODEL_DIR, "*"))):
            if os.path.isfile(f):
                z.write(f, os.path.basename(f))
    print("\n".join(report_lines))
    print("\n[outputs]")
    for f in sorted(glob.glob(os.path.join(MODEL_DIR, "*"))):
        print("  ", os.path.basename(f), os.path.getsize(f) // 1024, "KB")
    print("[zip]", zpath)


if __name__ == "__main__":
    main()