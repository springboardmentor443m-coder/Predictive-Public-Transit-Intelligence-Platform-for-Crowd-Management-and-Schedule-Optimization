"""Train crowd forecasting model: python -m app.ml.train_model"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.ml.data_loader import load_ridership_df
from app.ml.predictor import train
from app.core.config import settings

if __name__ == "__main__":
    df = load_ridership_df(settings.data_path)
    out = Path(__file__).resolve().parent / "model.pkl"
    metrics = train(df, out)
    print("Training metrics:", metrics)
    print(f"Model saved to {out}")
