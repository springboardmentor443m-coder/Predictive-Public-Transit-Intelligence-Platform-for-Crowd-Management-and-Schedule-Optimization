import glob
import json
import multiprocessing as mp
import os
import re
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
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    precision_recall_curve,
    r2_score,
    roc_auc_score,
    roc_curve,
)

DATASET_SLUG = "pranavbadami/nj-transit-amtrak-nec-performance"
DATASET_NAME = "nj_transit_delay"
OUT_DIR = "/kaggle/working" if os.path.isdir("/kaggle/working") else "."
MODEL_DIR = os.path.join(OUT_DIR, DATASET_NAME + "_outputs")
os.makedirs(MODEL_DIR, exist_ok=True)

RANDOM_STATE = 42
TEST_FRACTION = 0.20
MAX_ROWS = 3_000_000
PEAK_HOURS = {7, 8, 9, 16, 17, 18}
HOURS_PER_DAY = 24
N_ESTIMATORS = 400
EARLY_STOP = 25
N_THREADS = max(1, os.cpu_count() // 2)

XGB_MAJOR = int(xgb.__version__.split(".")[0])


def xgb_params(objective, eval_metric, extra=None):
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
        "objective": objective,
        "eval_metric": eval_metric,
    }
    if XGB_MAJOR >= 2:
        params["device"] = "cuda"
    else:
        params["tree_method"] = "gpu_hist"
    if extra:
        params.update(extra)
    return params


def delay_bucket(minutes):
    if pd.isna(minutes):
        return None
    if minutes <= 2:
        return "on_time"
    if minutes <= 6:
        return "minor_delay"
    return "delayed"


BUCKET_ORDER = ["on_time", "minor_delay", "delayed"]


def print_gpus():
    try:
        print(subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.free", "--format=csv"],
            capture_output=True, text=True, check=True).stdout)
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


def onehot(df, col, known):
    lookup = {v: i for i, v in enumerate(known)}
    idx = df[col].map(lookup)
    n = len(df)
    out = np.zeros((n, len(known)), dtype=np.float32)
    rows = np.flatnonzero(idx.notna().to_numpy())
    if rows.size:
        cols = idx.iloc[rows].astype(int).to_numpy()
        out[rows, cols] = 1.0
    return out


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
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual"); ax.set_title(title)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)
    return cm


def plot_roc_ovr(y_true, y_prob, classes, path):
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    scores = {}
    for i, c in enumerate(classes):
        y_c = (y_true == i).astype(int)
        if len(np.unique(y_c)) < 2:
            continue
        fpr, tpr, _ = roc_curve(y_c, y_prob[:, i])
        a = auc(fpr, tpr)
        scores[c] = float(a)
        ax.plot(fpr, tpr, label=f"{c} (AUC {a:.3f})")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4)
    ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
    ax.legend(loc="lower right"); ax.set_title("Delay classifier - one-vs-rest ROC")
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)
    return scores


def plot_pr_ovr(y_true, y_prob, classes, path):
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    scores = {}
    for i, c in enumerate(classes):
        y_c = (y_true == i).astype(int)
        if len(np.unique(y_c)) < 2:
            continue
        precision, recall, _ = precision_recall_curve(y_c, y_prob[:, i])
        scores[c] = float(auc(recall, precision))
        ax.plot(recall, precision, label=f"{c} (AP {scores[c]:.3f})")
    ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
    ax.legend(loc="upper right"); ax.set_title("Delay classifier - one-vs-rest PR")
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)
    return scores


def plot_scatter_resids(y_true, y_pred, title, prefix, out_dir, label_units, sample=200000):
    ix = np.random.RandomState(RANDOM_STATE).choice(len(y_true), size=min(sample, len(y_true)), replace=False)
    yt, yp = y_true[ix], y_pred[ix]
    fig, ax = plt.subplots(figsize=(6, 5.5))
    ax.scatter(yt, yp, s=6, alpha=0.12, rasterized=True)
    lo = min(yt.min(), yp.min()); hi = max(yt.max(), yp.max())
    ax.plot([lo, hi], [lo, hi], "r--", lw=1)
    ax.set_xlabel("Actual " + label_units); ax.set_ylabel("Predicted " + label_units)
    ax.set_title(title + " - actual vs predicted")
    fig.tight_layout(); fig.savefig(os.path.join(out_dir, prefix + "_scatter.png"), dpi=130); plt.close(fig)
    res = yt - yp
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.hist(res, bins=80, density=True, alpha=0.7, color="steelblue")
    ax.axvline(0, color="red", ls="--", lw=1)
    ax.set_xlabel("Residual (actual - predicted)"); ax.set_title(title + " - residuals")
    fig.tight_layout(); fig.savefig(os.path.join(out_dir, prefix + "_residuals.png"), dpi=130); plt.close(fig)


def plot_importance(model, feature_names, title, path, top=25):
    imp = np.asarray(model.feature_importances_, dtype=float)
    order = np.argsort(imp)[::-1][:top]
    names = [feature_names[i] for i in order]
    vals = imp[order]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(range(len(vals))[::-1], vals, color="steelblue")
    ax.set_yticks(range(len(vals))[::-1], names, fontsize=7)
    ax.set_xlabel("Feature importance"); ax.set_title(title)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)
    return dict(zip(names, vals.tolist()))


def fit_clf(X, y, eval_set, sample_weight, num_class):
    model = xgb.XGBClassifier(**xgb_params("multi:softprob", "mlogloss",
                                           {"num_class": num_class}))
    model.fit(X, y, eval_set=[eval_set], sample_weight=sample_weight, verbose=False)
    return model


def _train_runner(gpu_id, tag, fn, args, queue):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    t0 = time.time()
    try:
        result = fn(*args)
        result["tag"] = tag; result["gpu"] = gpu_id
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
        p.start(); procs.append(p)
    results = {}
    for _ in procs:
        tag, payload = queue.get()
        results[tag] = payload
    for p in procs:
        p.join()
    return results


def _save_artifact(path, artifact):
    joblib.dump(artifact, path)
    print("[save]", path)


DELAY_COL_ALIASES = ("delay_minutes", "delay_minute", "delay", "delay_min",
                     "delay_time", "lateness", "lateness_minutes")


def _norm_cols(cols):
    norm = []
    for c in cols:
        s = str(c).strip().lower()
        s = "".join(ch if ch.isalnum() else "_" for ch in s)
        norm.append(s.strip("_"))
    return norm


def _read_csv(path):
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            print(f"[data] encoding {enc} failed, trying next", flush=True)
    return pd.read_csv(path, encoding="latin-1")


def load_dataset():
    root = None
    files = search_input_files(["*.csv"])
    if files:
        files = [f for f in files if "invalid" not in os.path.basename(f).lower()
                 and re.search(r"\d{4}_\d{2}\.csv$", os.path.basename(f))]
    if not files:
        root = kagglehub_download(DATASET_SLUG)
        if root:
            files = [f for f in search_input_files(["*.csv"], root=root)
                     if "invalid" not in os.path.basename(f).lower()]
    if not files:
        raise RuntimeError("NJ Transit CSVs not found. Add the dataset via 'Add Data' or check the slug.")

    frames = []
    for f in files:
        df = _read_csv(f)
        norm = _norm_cols(df.columns)
        df.columns = norm
        delay_col = next((a for a in DELAY_COL_ALIASES if a in norm), None)
        if delay_col is None:
            print(f"[data] WARN no delay column in {os.path.basename(f)}: {df.columns.tolist()[:20]}",
                  flush=True)
            continue
        if delay_col != "delay_minutes":
            df = df.rename(columns={delay_col: "delay_minutes"})
        frames.append(df)
        print(f"[data] loaded {len(frames)}/{len(files)} monthly files: {os.path.basename(f)}", flush=True)
    if not frames:
        raise RuntimeError("No NJ Transit files with delay_minutes found.")
    return pd.concat(frames, ignore_index=True)


def prepare():
    raw = load_dataset()
    print("[data] raw rows:", len(raw))
    raw = raw.dropna(subset=["delay_minutes", "scheduled_time", "date"]).copy()
    raw["delay_minutes"] = pd.to_numeric(raw["delay_minutes"], errors="coerce")
    raw = raw.dropna(subset=["delay_minutes"])
    raw["delay_minutes"] = np.clip(raw["delay_minutes"], 0, None)
    if len(raw) > MAX_ROWS:
        raw = raw.sample(n=MAX_ROWS, random_state=RANDOM_STATE).reset_index(drop=True)

    raw["date_parsed"] = pd.to_datetime(raw["date"], errors="coerce")
    raw = raw.dropna(subset=["date_parsed"])
    raw["weekday"] = raw["date_parsed"].dt.weekday

    ts = pd.to_datetime(raw["scheduled_time"].astype(str).str.strip(), errors="coerce")
    raw["mins"] = ts.dt.hour * 60 + ts.dt.minute
    raw = raw.dropna(subset=["mins"])
    raw["hour"] = (raw["mins"].to_numpy() // 60).astype(int)

    raw["delay_bucket"] = raw["delay_minutes"].map(delay_bucket)
    raw = raw[raw["delay_bucket"].notna()]

    line_names = raw["line"].astype(str).value_counts().head(12).index.tolist()
    type_names = raw["type"].astype(str).value_counts().head(8).index.tolist()
    from_ids = raw["from_id"].astype(str).value_counts().head(100).index.tolist()
    to_ids = raw["to_id"].astype(str).value_counts().head(100).index.tolist()

    from_map = {v: i for i, v in enumerate(from_ids)}
    to_map = {v: i for i, v in enumerate(to_ids)}

    n = len(raw)
    t = temporal_block(raw["hour"].to_numpy(), raw["weekday"].to_numpy())
    mins = raw["mins"].to_numpy(dtype=np.float32)
    sched_sin = np.sin(2 * np.pi * mins / (24 * 60)).astype(np.float32).reshape(-1, 1)
    sched_cos = np.cos(2 * np.pi * mins / (24 * 60)).astype(np.float32).reshape(-1, 1)
    stop_seq = (raw["stop_sequence"].astype(float) / 50.0).clip(0, 2).to_numpy(dtype=np.float32).reshape(-1, 1)
    from_ord = raw["from_id"].astype(str).map(from_map).fillna(-1).to_numpy(dtype=np.float32).reshape(-1, 1)
    to_ord = raw["to_id"].astype(str).map(to_map).fillna(-1).to_numpy(dtype=np.float32).reshape(-1, 1)
    line_oh = onehot(pd.DataFrame({"line": raw["line"].astype(str)}), "line", line_names)
    type_oh = onehot(pd.DataFrame({"type": raw["type"].astype(str)}), "type", type_names)

    X = np.hstack([t, sched_sin, sched_cos, stop_seq, from_ord, to_ord, line_oh, type_oh]).astype(np.float32)
    feature_names = (["hour_sin", "hour_cos", "is_peak", "is_weekend", "dow_sin", "dow_cos",
                      "weekend_peak", "sched_sin", "sched_cos", "stop_sequence_norm",
                      "from_station", "to_station"]
                     + [f"line_{l}" for l in line_names] + [f"type_{t}" for t in type_names])

    labels = pd.Categorical(raw["delay_bucket"], categories=BUCKET_ORDER).codes
    y_cls = labels.astype(np.int32)
    y_reg = raw["delay_minutes"].to_numpy(dtype=np.float32)

    counts = np.bincount(labels, minlength=len(BUCKET_ORDER)).astype(float)
    weights = np.ones(len(labels), dtype=np.float32)
    for c in range(len(BUCKET_ORDER)):
        if counts[c] > 0:
            weights[labels == c] = counts.sum() / (len(BUCKET_ORDER) * counts[c])

    split_at = int(n * (1 - TEST_FRACTION))
    train_ix = np.arange(0, split_at, dtype=int)
    test_ix = np.arange(split_at, n, dtype=int)

    print("[data] nj rows:", n, "| class counts:", counts.astype(int).tolist())
    return {
        "X": X, "y_reg": y_reg, "y_cls": y_cls, "sample_weight": weights,
        "feature_names": feature_names, "classes": BUCKET_ORDER,
        "line_names": line_names, "type_names": type_names,
        "from_ids": from_ids, "to_ids": to_ids,
        "train_ix": train_ix, "test_ix": test_ix, "out_dir": MODEL_DIR,
    }


def _train_delay_cls(ctx, *_):
    X = ctx["X"]
    tr, te = ctx["train_ix"], ctx["test_ix"]
    y = ctx["y_cls"]
    w = ctx["sample_weight"]
    model = fit_clf(X[tr], y[tr], (X[te], y[te]), w[tr], len(ctx["classes"]))
    proba = model.predict_proba(X[te])
    pred = proba.argmax(axis=1)

    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
    metrics = {
        "accuracy": float(accuracy_score(y[te], pred)),
        "macro_precision": float(precision_score(y[te], pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y[te], pred, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y[te], pred, average="macro", zero_division=0)),
        "roc_auc": float(roc_auc_score(y[te], proba, multi_class="ovr", average="macro")),
    }
    cm = plot_confusion(y[te], pred, list(range(len(ctx["classes"]))),
                        "Delay status (actual vs predicted)",
                        os.path.join(MODEL_DIR, "delay_confusion.png"))
    metrics["confusion_matrix"] = cm.tolist()
    metrics["roc_per_class"] = plot_roc_ovr(y[te], proba, ctx["classes"],
                                            os.path.join(MODEL_DIR, "delay_roc.png"))
    metrics["pr_per_class"] = plot_pr_ovr(y[te], proba, ctx["classes"],
                                          os.path.join(MODEL_DIR, "delay_pr.png"))
    metrics["feature_importance"] = plot_importance(
        model, ctx["feature_names"], "Delay classifier - feature importance",
        os.path.join(MODEL_DIR, "delay_cls_importance.png"))
    metrics["classification_report"] = classification_report(
        y[te], pred, target_names=ctx["classes"], zero_division=0)
    metrics["best_iteration"] = int(getattr(model, "best_iteration", 0) or 0)

    sample_counts = np.bincount(y[te], minlength=len(ctx["classes"]))
    metrics["test_class_counts"] = sample_counts.astype(int).tolist()

    _save_artifact(os.path.join(MODEL_DIR, "delay_classifier.joblib"), {
        "model": model, "classes": ctx["classes"], "feature_names": ctx["feature_names"],
        "line_names": ctx["line_names"], "type_names": ctx["type_names"],
        "from_ids": ctx["from_ids"], "to_ids": ctx["to_ids"], "trained_on": DATASET_NAME,
    })
    return metrics


def _train_delay_reg(ctx, *_):
    X = ctx["X"]
    tr, te = ctx["train_ix"], ctx["test_ix"]
    y = ctx["y_reg"]
    model = xgb.XGBRegressor(**xgb_params("reg:squarederror", "rmse"))
    model.fit(X[tr], y[tr], eval_set=[(X[te], y[te])], verbose=False)
    preds = np.clip(model.predict(X[te]), 0, None)

    metrics = {
        "mae": float(mean_absolute_error(y[te], preds)),
        "rmse": float(np.sqrt(mean_squared_error(y[te], preds))),
        "r2": float(r2_score(y[te], preds)),
        "residual_std": float(np.std(y[te] - preds)),
    }
    plot_scatter_resids(y[te], preds, "Delay minutes", "delay_reg", MODEL_DIR, "min")
    metrics["feature_importance"] = plot_importance(
        model, ctx["feature_names"], "Delay regressor - feature importance",
        os.path.join(MODEL_DIR, "delay_reg_importance.png"))
    metrics["best_iteration"] = int(getattr(model, "best_iteration", 0) or 0)

    for label in ("on_time", "delayed"):
        pass
    delayed_mask = y[te] > 6
    if delayed_mask.any():
        metrics["delayed_only_mae"] = float(mean_absolute_error(y[te][delayed_mask], preds[delayed_mask]))

    _save_artifact(os.path.join(MODEL_DIR, "delay_regressor.joblib"), {
        "model": model, "feature_names": ctx["feature_names"],
        "line_names": ctx["line_names"], "type_names": ctx["type_names"],
        "from_ids": ctx["from_ids"], "to_ids": ctx["to_ids"], "trained_on": DATASET_NAME,
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
        ("delay_classifier", _train_delay_cls, (ctx,)),
        ("delay_regressor", _train_delay_reg, (ctx,)),
    ])

    report_lines = ["MetroFlow training report", DATASET_NAME, DATASET_SLUG, ""]
    for tag, res in sorted(results.items()):
        report_lines.append(f"--- {tag} ---")
        cls_rep = res.pop("classification_report", None)
        for k, v in res.items():
            if k == "confusion_matrix":
                report_lines.append("confusion_matrix: (see PNG)")
                continue
            report_lines.append(f"{k}: {v}")
        if cls_rep:
            report_lines.append("classification_report:")
            report_lines.append(cls_rep.rstrip())
        report_lines.append("")
    cm = results.get("delay_classifier", {}).get("confusion_matrix")
    if cm:
        report_lines.append("Confusion matrix (delay status, rows=actual, cols=predicted):")
        report_lines.append("  " + " ".join(f"{BUCKET_ORDER[i]:>12}" for i in range(len(BUCKET_ORDER))))
        for i, row in enumerate(cm):
            report_lines.append(f"{BUCKET_ORDER[i]:>12} " + " ".join(f"{c:12d}" for c in row))

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