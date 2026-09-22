import os
import sys
import joblib

model_paths = [
    os.path.abspath("../crowd_prediction_rf_compressed.pkl"),
    os.path.abspath("crowd_prediction_rf_compressed.pkl"),
]

found_path = None
for p in model_paths:
    if os.path.exists(p):
        found_path = p
        break

print(f"Searching for model artifact: {found_path}")
if not found_path:
    print("Model artifact not found!")
    sys.exit(1)

print(f"File size: {os.path.getsize(found_path) / (1024*1024):.2f} MB")
model = joblib.load(found_path)
print(f"Model type: {type(model)}")
print(f"Model parameters: {model.get_params()}")
if hasattr(model, "feature_names_in_"):
    print(f"Feature names ({len(model.feature_names_in_)}): {list(model.feature_names_in_)}")
if hasattr(model, "n_features_in_"):
    print(f"Number of features: {model.n_features_in_}")
if hasattr(model, "n_estimators"):
    print(f"Number of estimators: {model.n_estimators}")
if hasattr(model, "oob_score_"):
    print(f"OOB score: {model.oob_score_}")
else:
    print("OOB score: Not computed / oob_score=False")
