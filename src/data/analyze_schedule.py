import pandas as pd

input_path = "data/raw/mta_schedule_2025_05_01.csv"

df = pd.read_csv(input_path)

print("Total schedule rows:", len(df))

# Convert revenue_service to numeric
df["revenue_service"] = pd.to_numeric(
    df["revenue_service"],
    errors="coerce"
)

print("\nRevenue service:")
print(df["revenue_service"].value_counts(dropna=False))

# Keep only revenue-service trains
revenue = df[df["revenue_service"] == 1].copy()

print("\nRevenue-service schedule rows:", len(revenue))

print("\nUnique trains:")
print(df["train_id"].nunique())

print("\nUnique revenue-service trains:")
print(revenue["train_id"].nunique())

print("\nUnique GTFS stops:")
print(revenue["gtfs_stop_id"].nunique())

print("\nUnique lines:")
print(revenue["line"].nunique())

print("\nRows by line:")
print(
    revenue.groupby("line")["train_id"]
    .nunique()
    .sort_values(ascending=False)
)

print("\nSchedule sample:")
print(
    revenue[
        [
            "service_date",
            "train_id",
            "line",
            "direction",
            "stop_order",
            "gtfs_stop_id",
            "departure_time",
            "revenue_service"
        ]
    ].head(20)
)