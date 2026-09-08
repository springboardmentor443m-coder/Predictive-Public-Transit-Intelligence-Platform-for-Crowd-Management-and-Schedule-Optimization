import pandas as pd

# Load cleaned data
df = pd.read_csv("data/cleaned_data.csv")

# Convert Datetime column
df["Datetime"] = pd.to_datetime(df["Datetime"])

# ==========================
# Time-based Features
# ==========================

df["hour"] = df["Datetime"].dt.hour
df["day"] = df["Datetime"].dt.day
df["month"] = df["Datetime"].dt.month
df["year"] = df["Datetime"].dt.year
df["day_of_week"] = df["Datetime"].dt.dayofweek

# ==========================
# Weekend Feature
# ==========================

df["is_weekend"] = (
    df["day_of_week"] >= 5
).astype(int)

# ==========================
# Peak Hour Feature
# ==========================
# Morning Rush: 7,8,9
# Evening Rush: 16,17,18,19

df["is_peak_hour"] = (
    df["hour"].isin(
        [7, 8, 9, 16, 17, 18, 19]
    )
).astype(int)

# ==========================
# Total Passenger Traffic
# ==========================

df["Total_Traffic"] = (
    df["Entries"] + df["Exits"]
)

# ==========================
# Congestion Level
# ==========================

q1 = df["Total_Traffic"].quantile(0.33)
q2 = df["Total_Traffic"].quantile(0.66)

def congestion_level(x):
    if x <= q1:
        return "Low"
    elif x <= q2:
        return "Medium"
    else:
        return "High"

df["Congestion_Level"] = (
    df["Total_Traffic"]
    .apply(congestion_level)
)

# ==========================
# Optional Cleanup
# ==========================

# Direction labels have many missing values and
# are not useful for crowd prediction.

df.drop(
    columns=[
        "North Direction Label",
        "South Direction Label"
    ],
    inplace=True,
    errors="ignore"
)

# ==========================
# Save Feature Dataset
# ==========================

df.to_csv(
    "data/features.csv",
    index=False
)

# ==========================
# Verification
# ==========================

print("Feature Engineering Completed Successfully")
print("\nDataset Shape:", df.shape)

print("\nCongestion Level Distribution:")
print(df["Congestion_Level"].value_counts())

print("\nNew Columns Added:")
print([
    "hour",
    "day",
    "month",
    "year",
    "day_of_week",
    "is_weekend",
    "is_peak_hour",
    "Total_Traffic",
    "Congestion_Level"
])