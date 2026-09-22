import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    confusion_matrix, precision_recall_curve
)

model = joblib.load("delay_prediction_rf_v2.pkl")
le_season = joblib.load("le_season.pkl")
le_weather = joblib.load("le_weather.pkl")

print(f"Delay Model Type: {type(model).__name__}")
print(f"Number of estimators: {len(model.estimators_)}")
print(f"Max depth: {model.max_depth}")
print(f"Classes: {model.classes_}")
print(f"Class weight: {model.class_weight}")
print(f"Features ({len(model.feature_names_in_)}): {list(model.feature_names_in_)}")
print(f"Seasons ({len(le_season.classes_)}): {list(le_season.classes_)}")
print(f"Weather classes ({len(le_weather.classes_)}): {list(le_weather.classes_)}")

# Check leaf values and tree structures
all_leaves_class1_probs = []
for tree in model.estimators_:
    tree_values = tree.tree_.value # shape: (n_nodes, 1, n_classes)
    # class 0 count, class 1 count (weighted)
    c0 = tree_values[:, 0, 0]
    c1 = tree_values[:, 0, 1]
    total = c0 + c1
    prob1 = np.divide(c1, total, out=np.zeros_like(c1), where=total > 0)
    # get leaves only
    is_leaf = (tree.tree_.children_left == -1) & (tree.tree_.children_right == -1)
    all_leaves_class1_probs.extend(prob1[is_leaf])

all_leaves_class1_probs = np.array(all_leaves_class1_probs)
print(f"\nTree Leaf Class 1 (Delay) Probability Distribution across all {len(model.estimators_)} trees:")
print(f"  Min leaf prob: {all_leaves_class1_probs.min():.4f}")
print(f"  Max leaf prob: {all_leaves_class1_probs.max():.4f}")
print(f"  Mean leaf prob: {all_leaves_class1_probs.mean():.4f}")
print(f"  % leaves with prob >= 0.70: {(all_leaves_class1_probs >= 0.70).mean()*100:.2f}%")
