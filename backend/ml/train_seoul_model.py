import os
import csv
import pickle
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "metroflow_processed_network.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

print("=" * 65)
print("[*] Training MetroFlow Random Forest (Dictionary Export Mode)...")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    records = list(reader)

X = []
y = []
for r in records:
    X.append([
        int(r["station_code"]),
        int(r["hour"]),
        int(r["day_of_week"]),
        int(r["is_weekend"]),
        int(r["is_peak_hour"]),
        float(r["exits"])
    ])
    y.append(float(r["entries"]))

def build_tree(X_sub, y_sub, depth=0, max_depth=7):
    if not y_sub:
        return {"val": 0.0}
    val = sum(y_sub) / len(y_sub)
    if depth >= max_depth or len(y_sub) < 20:
        return {"val": val}

    best_feat, best_thresh, best_red = None, None, 0.0
    curr_var = sum((v - val) ** 2 for v in y_sub)

    for f_idx in [1, 4, 5, 0]:
        vals = [row[f_idx] for row in X_sub]
        min_v, max_v = min(vals), max(vals)
        if min_v == max_v:
            continue
        for s in range(1, 5):
            th = min_v + s * (max_v - min_v) / 5.0
            left_y = [y_sub[i] for i, r in enumerate(X_sub) if r[f_idx] <= th]
            right_y = [y_sub[i] for i, r in enumerate(X_sub) if r[f_idx] > th]
            if not left_y or not right_y:
                continue
            v_after = sum((v - sum(left_y)/len(left_y))**2 for v in left_y) + sum((v - sum(right_y)/len(right_y))**2 for v in right_y)
            red = curr_var - v_after
            if red > best_red:
                best_red, best_feat, best_thresh = red, f_idx, th

    if best_feat is not None:
        left_X = [r for r in X_sub if r[best_feat] <= best_thresh]
        left_y = [y_sub[i] for i, r in enumerate(X_sub) if r[best_feat] <= best_thresh]
        right_X = [r for r in X_sub if r[best_feat] > best_thresh]
        right_y = [y_sub[i] for i, r in enumerate(X_sub) if r[best_feat] > best_thresh]
        return {
            "feat": best_feat,
            "th": best_thresh,
            "left": build_tree(left_X, left_y, depth + 1, max_depth),
            "right": build_tree(right_X, right_y, depth + 1, max_depth)
        }
    return {"val": val}

# Train 10 trees
random.seed(42)
n_samples = len(X)
forest_trees = []

for i in range(10):
    print(f"[*] Building Forest Tree {i+1}/10...")
    indices = [random.randint(0, n_samples - 1) for _ in range(n_samples // 2)]
    X_boot = [X[idx] for idx in indices]
    y_boot = [y[idx] for idx in indices]
    forest_trees.append(build_tree(X_boot, y_boot))

model_payload = {
    "model_name": "MetroFlowRandomForest",
    "trees": forest_trees,
    "feature_order": ["station_code", "hour", "day_of_week", "is_weekend", "is_peak_hour", "exits"]
}

model_save_path = os.path.join(MODEL_DIR, "crowd_predictor.pkl")
with open(model_save_path, "wb") as f:
    pickle.dump(model_payload, f)

print(f"\n[✓] Saved standalone Random Forest model artifact to:\n    {model_save_path}\n")