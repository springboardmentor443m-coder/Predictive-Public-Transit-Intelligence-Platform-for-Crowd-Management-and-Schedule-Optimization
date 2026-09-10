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

plt.title("Total Ridership by Hour")
plt.xlabel("Hour of Day")
plt.ylabel("Total Ridership")

plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig("outputs/hourly_ridership.png")
plt.show()

# Top 10 busiest stations graph
top_10_stations = station_ridership.head(10)

top_10_stations.sort_values().plot(
    kind="barh",
    figsize=(10, 6)
)

plt.title("Top 10 Stations by Total Ridership")
plt.xlabel("Total Ridership")
plt.ylabel("Station")
plt.tight_layout()

plt.savefig("outputs/top_10_stations.png")
plt.show()

# Daily ridership analysis
daily_ridership = df.groupby("Date")["Ridership"].sum().sort_index()

print("\nDaily ridership:")
print(daily_ridership)

print("\nHighest ridership day:")
print(daily_ridership.idxmax(), "with", daily_ridership.max(), "passengers")

print("\nLowest ridership day:")
print(daily_ridership.idxmin(), "with", daily_ridership.min(), "passengers")

# Daily ridership graph
daily_ridership.plot(
    kind="line",
    figsize=(12, 5),
    marker="o"
)

plt.title("Daily Total Ridership")
plt.xlabel("Date")
plt.ylabel("Total Ridership")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig("outputs/daily_ridership.png")
plt.show()

# Peak and off-peak period analysis

def classify_period(hour):
    if 7 <= hour <= 10:
        return "Morning Peak"
    elif 17 <= hour <= 20:
        return "Evening Peak"
    elif 11 <= hour <= 16:
        return "Midday"
    else:
        return "Off-Peak"


df["Period"] = df["Hour"].apply(classify_period)

period_ridership = df.groupby("Period")["Ridership"].agg(
    Total_Ridership="sum",
    Average_Ridership="mean"
)

print("\nRidership by period:")
print(period_ridership)

print("\nPeriod with highest total ridership:")
print(period_ridership["Total_Ridership"].idxmax())

print("\nPeriod with highest average ridership:")
print(period_ridership["Average_Ridership"].idxmax())

# Period-wise ridership graph
period_ridership["Total_Ridership"].sort_values(ascending=False).plot(
    kind="bar",
    figsize=(9, 5)
)

plt.title("Ridership by Time Period")
plt.xlabel("Time Period")
plt.ylabel("Total Ridership")
plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig("outputs/period_ridership.png")
plt.show()

# Weekday vs weekend analysis

df["Date"] = pd.to_datetime(df["Date"])

df["Day"] = df["Date"].dt.day_name()

day_ridership = df.groupby("Day")["Ridership"].agg(
    Total_Ridership="sum",
    Average_Ridership="mean"
)

# Arrange days in calendar order
day_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

day_ridership = day_ridership.reindex(day_order)

print("\nRidership by day of week:")
print(day_ridership)

print("\nDay with highest average ridership:")
print(day_ridership["Average_Ridership"].idxmax())

print(
    "Average ridership:",
    day_ridership["Average_Ridership"].max()
)

# Weekday vs weekend classification
df["Day_Type"] = df["Date"].dt.dayofweek.apply(
    lambda x: "Weekend" if x >= 5 else "Weekday"
)

day_type_ridership = df.groupby("Day_Type")["Ridership"].agg(
    Total_Ridership="sum",
    Average_Ridership="mean"
)

print("\nWeekday vs Weekend ridership:")
print(day_type_ridership)

# Day-of-week graph
day_ridership["Average_Ridership"].plot(
    kind="bar",
    figsize=(10, 5)
)

plt.title("Average Ridership by Day of Week")
plt.xlabel("Day of Week")
plt.ylabel("Average Ridership")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig("outputs/day_of_week_ridership.png")
plt.show()