import pandas as pd

# Load BMRCL hourly ridership dataset
file_path = "data/bmrcl/station-hourly.csv"

df = pd.read_csv(file_path,sep = ";")

# Display first 5 rows
print("First 5 rows:")
print(df.head())

# Display number of rows and columns
print("\nDataset shape:")
print(df.shape)

# Display column names
print("\nColumn names:")
print(df.columns.tolist())

# Display data types and non-null information
print("\nDataset information:")
print(df.info())


# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())

# Check for duplicate rows
print("\nDuplicate rows:")
print(df.duplicated().sum())


# Basic dataset details
print("\nNumber of unique stations:")
print(df["Station"].nunique())

print("\nNumber of unique dates:")
print(df["Date"].nunique())

print("\nHour range:")
print(df["Hour"].min(), "to", df["Hour"].max())

print("\nSample station names:")
print(df["Station"].unique()[:10])


# Hourly ridership analysis
hourly_ridership = df.groupby("Hour")["Ridership"].sum()

print("\nHourly ridership:")
print(hourly_ridership)

print("\nPeak hour:")
print(hourly_ridership.idxmax(), "with", hourly_ridership.max(), "passengers")

print("\nLowest ridership hour:")
print(hourly_ridership.idxmin(), "with", hourly_ridership.min(), "passengers")

# Station-wise ridership analysis
station_ridership = df.groupby("Station")["Ridership"].sum().sort_values(ascending=False)

print("\nTop 10 stations by total ridership:")
print(station_ridership.head(10))

print("\nBottom 10 stations by total ridership:")
print(station_ridership.tail(10))

# Peak and off-peak analysis

# Calculate average ridership for each hour
hourly_average = df.groupby("Hour")["Ridership"].mean().sort_values(ascending=False)

print("\nAverage ridership by hour:")
print(hourly_average)

# Top 5 busiest hours
print("\nTop 5 peak hours:")
print(hourly_average.head(5))

# Bottom 5 hours by ridership
print("\nBottom 5 hours:")
print(hourly_average.tail(5))

# Overall average hourly ridership
overall_average = df["Ridership"].mean()

print("\nOverall average ridership per record:")
print(overall_average)

# Classify hours into demand periods

def classify_period(hour):
    if 7 <= hour <= 10:
        return "Morning Peak"
    elif 17 <= hour <= 20:
        return "Evening Peak"
    elif 11 <= hour <= 16:
        return "Midday"
    else:
        return "Night"


df["Period"] = df["Hour"].apply(classify_period)

# Calculate ridership by period
period_ridership = df.groupby("Period")["Ridership"].agg(
    ["sum", "mean", "count"]
).sort_values("sum", ascending=False)

print("\nRidership by demand period:")
print(period_ridership)

# Hourly ridership graph

import matplotlib.pyplot as plt

hourly_ridership.plot(kind="bar", figsize=(10, 5))

plt.title("Average Ridership by Hour")
plt.xlabel("Hour of Day")
plt.ylabel("Average Ridership")

plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig("outputs/hourly_ridership.png")
plt.show()