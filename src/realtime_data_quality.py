import os
import pandas as pd


# =========================================================
# SETTINGS
# =========================================================

REALTIME_FILE = (
    "data/realtime/vline_vehicle_history.csv"
)

OUTPUT_FILE = (
    "data/realtime/realtime_data_quality.csv"
)


# =========================================================
# HEADER
# =========================================================

print("========================================")
print("REALTIME DATA QUALITY ANALYSIS")
print("========================================")


# =========================================================
# LOAD REALTIME HISTORY
# =========================================================

print("\nLoading realtime vehicle history...")

if not os.path.exists(REALTIME_FILE):
    raise FileNotFoundError(
        f"Realtime file not found: {REALTIME_FILE}"
    )

df = pd.read_csv(REALTIME_FILE)

print(
    "Realtime observations loaded:",
    len(df)
)


if df.empty:
    raise ValueError(
        "Realtime history contains no observations."
    )


# =========================================================
# REQUIRED COLUMNS
# =========================================================

required_columns = [
    "collection_time",
    "vehicle_id",
    "trip_id",
    "latitude",
    "longitude",
    "vehicle_timestamp",
    "feed_timestamp",
    "status"
]

for column in required_columns:
    if column not in df.columns:
        raise ValueError(
            f"Missing required column: {column}"
        )


# =========================================================
# CLEAN DATA
# =========================================================

df["collection_time"] = pd.to_datetime(
    df["collection_time"],
    errors="coerce",
    utc=True
)

df["vehicle_timestamp"] = pd.to_numeric(
    df["vehicle_timestamp"],
    errors="coerce"
)

df["feed_timestamp"] = pd.to_numeric(
    df["feed_timestamp"],
    errors="coerce"
)

df["latitude"] = pd.to_numeric(
    df["latitude"],
    errors="coerce"
)

df["longitude"] = pd.to_numeric(
    df["longitude"],
    errors="coerce"
)


# =========================================================
# VEHICLE TIMESTAMP → DATETIME
# =========================================================

df["vehicle_datetime"] = pd.to_datetime(
    df["vehicle_timestamp"],
    unit="s",
    errors="coerce",
    utc=True
)


# =========================================================
# FEED TIMESTAMP → DATETIME
# =========================================================

df["feed_datetime"] = pd.to_datetime(
    df["feed_timestamp"],
    unit="s",
    errors="coerce",
    utc=True
)


# =========================================================
# TIMESTAMP AGE
# =========================================================

df["vehicle_timestamp_age_seconds"] = (
    df["collection_time"]
    - df["vehicle_datetime"]
).dt.total_seconds()


df["feed_timestamp_age_seconds"] = (
    df["collection_time"]
    - df["feed_datetime"]
).dt.total_seconds()


# =========================================================
# TIMESTAMP CHANGE
# =========================================================

df = df.sort_values(
    [
        "vehicle_id",
        "collection_time"
    ]
).reset_index(drop=True)


df["vehicle_timestamp_changed"] = (
    df.groupby("vehicle_id")[
        "vehicle_timestamp"
    ]
    .transform(
        lambda x: x.ne(x.shift())
    )
)


df["feed_timestamp_changed"] = (
    df.groupby("vehicle_id")[
        "feed_timestamp"
    ]
    .transform(
        lambda x: x.ne(x.shift())
    )
)


# First observation is not evidence of a change.
df.loc[
    df.groupby("vehicle_id").cumcount() == 0,
    "vehicle_timestamp_changed"
] = False

df.loc[
    df.groupby("vehicle_id").cumcount() == 0,
    "feed_timestamp_changed"
] = False


# =========================================================
# POSITION CHANGE
# =========================================================

df["latitude_changed"] = (
    df.groupby("vehicle_id")[
        "latitude"
    ]
    .transform(
        lambda x: x.ne(x.shift())
    )
)

df["longitude_changed"] = (
    df.groupby("vehicle_id")[
        "longitude"
    ]
    .transform(
        lambda x: x.ne(x.shift())
    )
)


df["position_changed"] = (
    df["latitude_changed"]
    | df["longitude_changed"]
)


df.loc[
    df.groupby("vehicle_id").cumcount() == 0,
    "position_changed"
] = False


# =========================================================
# DATA QUALITY STATUS
# =========================================================

def determine_quality(row):

    # Missing timestamps
    if pd.isna(row["vehicle_timestamp"]):
        return "MISSING_VEHICLE_TIMESTAMP"

    if pd.isna(row["feed_timestamp"]):
        return "MISSING_FEED_TIMESTAMP"

    # Vehicle timestamp older than 5 minutes
    if (
        row["vehicle_timestamp_age_seconds"]
        > 300
    ):
        return "STALE_VEHICLE_TIMESTAMP"

    # Vehicle timestamp appears to be in future
    if (
        row["vehicle_timestamp_age_seconds"]
        < -60
    ):
        return "FUTURE_VEHICLE_TIMESTAMP"

    # Position is changing and timestamp is usable
    if row["position_changed"]:
        return "USABLE_MOVING_DATA"

    # Position is unchanged but timestamp is changing
    if row["vehicle_timestamp_changed"]:
        return "USABLE_STATIONARY_DATA"

    # Nothing changes
    return "REPEATED_OBSERVATION"


df["quality_status"] = df.apply(
    determine_quality,
    axis=1
)


# =========================================================
# PREDICTION USABILITY
# =========================================================

def determine_prediction_usability(row):

    if row["quality_status"] in [
        "MISSING_VEHICLE_TIMESTAMP",
        "MISSING_FEED_TIMESTAMP",
        "STALE_VEHICLE_TIMESTAMP",
        "FUTURE_VEHICLE_TIMESTAMP"
    ]:
        return "NOT_USABLE"

    if row["quality_status"] in [
        "USABLE_MOVING_DATA",
        "USABLE_STATIONARY_DATA"
    ]:
        return "USABLE"

    return "LIMITED"


df["prediction_usability"] = df.apply(
    determine_prediction_usability,
    axis=1
)


# =========================================================
# SUMMARY
# =========================================================

print("\n========================================")
print("DATA QUALITY SUMMARY")
print("========================================")

print(
    "Total observations:",
    len(df)
)


print("\nQuality status counts:")

print(
    df["quality_status"]
    .value_counts()
    .to_string()
)


print("\nPrediction usability counts:")

print(
    df["prediction_usability"]
    .value_counts()
    .to_string()
)


# =========================================================
# TIMESTAMP SUMMARY
# =========================================================

print("\n========================================")
print("TIMESTAMP ANALYSIS")
print("========================================")


vehicle_timestamps = (
    df["vehicle_timestamp"]
    .dropna()
    .nunique()
)

feed_timestamps = (
    df["feed_timestamp"]
    .dropna()
    .nunique()
)

position_count = (
    df[
        "position_changed"
    ]
    .sum()
)


print(
    "Unique vehicle timestamps:",
    vehicle_timestamps
)

print(
    "Unique feed timestamps:",
    feed_timestamps
)

print(
    "Observations with position change:",
    int(position_count)
)


# =========================================================
# AGE STATISTICS
# =========================================================

valid_vehicle_age = df[
    "vehicle_timestamp_age_seconds"
].dropna()


if not valid_vehicle_age.empty:

    print(
        "\nVehicle timestamp age:"
    )

    print(
        "Minimum:",
        round(
            valid_vehicle_age.min(),
            2
        ),
        "seconds"
    )

    print(
        "Maximum:",
        round(
            valid_vehicle_age.max(),
            2
        ),
        "seconds"
    )

    print(
        "Average:",
        round(
            valid_vehicle_age.mean(),
            2
        ),
        "seconds"
    )


# =========================================================
# VEHICLE SUMMARY
# =========================================================

print("\n========================================")
print("VEHICLE SUMMARY")
print("========================================")


vehicle_summary = (
    df.groupby("vehicle_id")
    .agg(
        observations=(
            "vehicle_id",
            "size"
        ),
        unique_vehicle_timestamps=(
            "vehicle_timestamp",
            "nunique"
        ),
        unique_feed_timestamps=(
            "feed_timestamp",
            "nunique"
        ),
        position_changes=(
            "position_changed",
            "sum"
        ),
        usable_observations=(
            "prediction_usability",
            lambda x: (
                x == "USABLE"
            ).sum()
        ),
        not_usable_observations=(
            "prediction_usability",
            lambda x: (
                x == "NOT_USABLE"
            ).sum()
        )
    )
    .reset_index()
)


print(
    vehicle_summary.to_string(
        index=False
    )
)


# =========================================================
# DETAILED RESULTS
# =========================================================

print("\n========================================")
print("DETAILED DATA QUALITY RESULTS")
print("========================================")


display_columns = [
    "collection_time",
    "vehicle_id",
    "trip_id",
    "latitude",
    "longitude",
    "vehicle_timestamp",
    "feed_timestamp",
    "vehicle_timestamp_age_seconds",
    "vehicle_timestamp_changed",
    "position_changed",
    "quality_status",
    "prediction_usability"
]


print(
    df[display_columns]
    .tail(20)
    .to_string(index=False)
)


# =========================================================
# SAVE RESULTS
# =========================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)


df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\nSaved results to:")

print(OUTPUT_FILE)


print(
    "\nRealtime data quality analysis "
    "completed successfully!"
)