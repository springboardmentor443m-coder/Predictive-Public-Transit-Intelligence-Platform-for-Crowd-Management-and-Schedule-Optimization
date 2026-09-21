import pandas as pd
from sklearn.ensemble import RandomForestRegressor

# Load dataset
df = pd.read_csv("../dataset/station-hourly.csv", sep=";")

# Convert Date
df["Date"] = pd.to_datetime(df["Date"])

# Create date features
df["year"] = df["Date"].dt.year
df["month"] = df["Date"].dt.month
df["day"] = df["Date"].dt.day
df["day_of_week"] = df["Date"].dt.dayofweek

# Create station codes
df["station_code"] = df["Station"].astype("category").cat.codes

# Features
X = df[
    [
        "Hour",
        "year",
        "month",
        "day",
        "day_of_week",
        "station_code"
    ]
]

# Target
y = df["Ridership"]

# Create model
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

# Train model
model.fit(X, y)

print("Random Forest model trained successfully!")