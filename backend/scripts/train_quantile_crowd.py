"""Train a quantile GradientBoosting crowd-occupancy model with native
confidence intervals.

Trains three GradientBoostingRegressors (``loss="quantile"``) at alpha
0.05 / 0.50 / 0.95 on the generated ``data/ridership_hourly.csv`` using the
Hangzhou station codes and the same feature schema the API uses at inference
time (``app.ml.features.kaggle_row_features``), so the artifact plugs into the
existing ``CrowdModel`` wrapper without any API change.

Output: ``models_store/hangzhou_crowd_quantile_model.joblib``
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.ensemble import GradientBoostingRegressor  # noqa: E402
from sklearn.metrics import mean_absolute_error, r2_score  # noqa: E402

from app.ml import features as feat  # noqa: E402
from app.ml import registry  # noqa: E402

STORE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models_store"
)
ARTIFACT_FILE = "hangzhou_crowd_quantile_model.joblib"
CAP_NORM_SCALE = 700.0
ALPHAS = (0.05, 0.50, 0.95)
RANDOM_STATE = 42
TEST_FRACTION = 0.20
DEFAULT_ESTIMATORS = 250
DEFAULT_DEPTH = 5


def load_and_encode(csv_path: str):
    df = pd.read_csv(csv_path)
    mapping = registry.CITY_STATION_MAP["hangzhou"]
    codes = sorted(mapping.values())
    df["code"] = df["station_code"].map(mapping)
    train = df.dropna(subset=["code"]).copy()
    n_before, n_after = len(df), len(train)
    if n_after < n_before:
        print(f"[data] dropped {n_before - n_after} rows with unmapped stations "
              f"(kept {n_after})")
    train["weekday"] = train["weekday"].astype(int)
    train["hour"] = train["hour"].astype(int)
    y = (train["occupancy_pct"] / 100.0).to_numpy(dtype=np.float32)
    X = np.array([
        feat.kaggle_row_features(
            int(h), int(wd), code, cap, codes, CAP_NORM_SCALE
        )
        for h, wd, code, cap in zip(
            train["hour"], train["weekday"], train["code"], train["capacity"]
        )
    ])
    feature_names = (
        ["hour_sin", "hour_cos", "is_peak", "is_weekend", "dow_sin", "dow_cos", "weekend_peak"]
        + [f"station_{c}" for c in codes]
        + ["capacity_norm"]
    )
    return train, X, y, codes, feature_names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ridership_hourly.csv"
    ), help="Input ridership CSV (generate_data.py schema)")
    parser.add_argument("--estimators", type=int, default=DEFAULT_ESTIMATORS)
    parser.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    parser.add_argument("--out", default=os.path.join(STORE_DIR, ARTIFACT_FILE))
    args = parser.parse_args()

    train, X, y, codes, feature_names = load_and_encode(args.csv)
    n = len(train)
    print(f"[data] {n} usable station-hour rows | {len(codes)} codes | features {X.shape[1]}")
    if n == 0:
        raise SystemExit("No training rows; nothing to do.")

    split = int(n * (1 - TEST_FRACTION))
    idx = np.arange(n)
    rng = np.random.default_rng(RANDOM_STATE)
    rng.shuffle(idx)
    tr, te = idx[:split], idx[split:]

    models = {}
    metrics = {}
    for alpha in ALPHAS:
        tag = "center" if alpha == 0.50 else ("low" if alpha == 0.05 else "high")
        print(f"[train] quantile alpha={alpha:0.2f} ...")
        gbr = GradientBoostingRegressor(
            loss="quantile",
            alpha=alpha,
            n_estimators=args.estimators,
            max_depth=args.depth,
            learning_rate=0.08,
            subsample=0.9,
            random_state=RANDOM_STATE,
        )
        gbr.fit(X[tr], y[tr])
        preds = gbr.predict(X[te])
        if alpha == 0.50:
            metrics["mae"] = round(float(mean_absolute_error(y[te], preds)), 4)
            metrics["r2"] = round(float(r2_score(y[te], preds)), 4)
            metrics["residual_std"] = round(float(np.std(y[te] - preds)), 4)
        models[tag] = gbr
        print(f"[train] alpha={alpha:0.2f} done")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    try:
        import joblib
    except ImportError:
        raise SystemExit("joblib not installed")
    joblib.dump({
        "model": models["center"],
        "low": models["low"],
        "high": models["high"],
        "kind": "quantile",
        "alphas": [0.05, 0.50, 0.95],
        "stations": codes,
        "feature_names": feature_names,
        "cap_norm_scale": CAP_NORM_SCALE,
        "residual_std": metrics["residual_std"],
        "trained_on": "hangzhou",
        "n_rows": int(n),
    }, args.out)
    print(f"[save] {args.out}")
    print(f"[metrics] MAE={metrics['mae']} R2={metrics['r2']} residual_std={metrics['residual_std']}")


if __name__ == "__main__":
    main()