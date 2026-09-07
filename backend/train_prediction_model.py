import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

print("Training demand forecasting model...")
crowd_file = os.path.join("data", "crowd_data.csv")
df = pd.read_csv(crowd_file, nrows=25000)

# Detect time and entry columns
time_col = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()][0]
entry_col = [c for c in df.columns if any(k in c.lower() for k in ['entry', 'entries', 'inflow', 'board'])][0]

df['timestamp'] = pd.to_datetime(df[time_col], errors='coerce')
df = df.dropna(subset=['timestamp'])

# Feature Engineering: hour of day and day of week
df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.dayofweek
df['inflow'] = pd.to_numeric(df[entry_col], errors='coerce').abs().fillna(150)

X = df[['hour', 'day_of_week']]
y = df['inflow']

model = RandomForestRegressor(n_estimators=35, random_state=42)
model.fit(X, y)

os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/demand_forecast_model.pkl")
print("Model saved to backend/models/demand_forecast_model.pkl")