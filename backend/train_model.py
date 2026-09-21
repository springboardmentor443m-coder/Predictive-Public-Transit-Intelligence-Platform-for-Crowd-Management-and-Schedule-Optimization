import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from app.data_generator import generate_datasets, seed_database

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "datasets")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "crowd_model.pkl")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "encoders.pkl")

def train_ai_model():
    csv_path = os.path.join(DATASETS_DIR, "metro_ridership_dataset.csv")
    if not os.path.exists(csv_path):
        print("Dataset not found. Generating new datasets...")
        generate_datasets()
        seed_database()
        
    df = pd.read_csv(csv_path)
    
    # Feature engineering
    le_station = LabelEncoder()
    df["station_encoded"] = le_station.fit_transform(df["station_id"])
    
    X = df[["station_encoded", "day_of_week", "hour_of_day", "is_weekend", "is_peak_hour"]]
    y = df["current_occupancy"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"Model Training Complete!")
    print(f"Train R^2 Score: {train_score:.4f}")
    print(f"Test R^2 Score:  {test_score:.4f}")
    
    # Save model and encoders
    joblib.dump(model, MODEL_PATH)
    joblib.dump({"station_encoder": le_station}, ENCODER_PATH)
    print(f"Saved AI model to {MODEL_PATH}")

if __name__ == "__main__":
    train_ai_model()
