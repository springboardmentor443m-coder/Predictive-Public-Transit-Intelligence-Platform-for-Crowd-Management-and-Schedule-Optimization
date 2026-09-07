import os
import joblib
import torch
import torch.nn as nn
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from app.ml.data_generator import generate_synthetic_transit_dataset

SAVED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
PROCESSED_DATASET = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "datasets", "processed", "master_transit_dataset.csv")
)
os.makedirs(SAVED_MODELS_DIR, exist_ok=True)


class LSTMAnomalyDetector(nn.Module):
    def __init__(self, input_dim=8, hidden_dim=32, num_layers=2):
        super(LSTMAnomalyDetector, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return self.sigmoid(out)


def train_crowd_anomaly_models():
    if os.path.exists(PROCESSED_DATASET):
        print(f"Loading real-world master dataset from {PROCESSED_DATASET}...")
        df = pd.read_csv(PROCESSED_DATASET)
    else:
        print("Generating dataset for PyTorch/RandomForest Congestion Predictor...")
        df = generate_synthetic_transit_dataset(days=14)

    feature_cols = [
        "hour",
        "minute",
        "day_of_week",
        "is_weekend",
        "inflow_ppm",
        "outflow_ppm",
        "line_delay_min",
        "density_pct",
    ]

    X = df[feature_cols]
    y = df["target_congestion_level"].map({"NORMAL": 0, "MODERATE": 1, "CRITICAL": 2})

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)

    rf_path = os.path.join(SAVED_MODELS_DIR, "crowd_classifier.joblib")
    joblib.dump({"model": clf, "features": feature_cols, "dataset_rows": len(df)}, rf_path)
    print(f"Saved Random Forest Crowd Classifier to {rf_path}")

    lstm_model = LSTMAnomalyDetector(input_dim=len(feature_cols))
    lstm_model.eval()

    torch_path = os.path.join(SAVED_MODELS_DIR, "lstm_anomaly_model.pt")
    torch.save(lstm_model.state_dict(), torch_path)
    print(f"Saved PyTorch LSTM model weights to {torch_path}")


if __name__ == "__main__":
    train_crowd_anomaly_models()
