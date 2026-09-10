import pandas as pd

ridership_path = "data/processed/station_hourly_ridership.csv"
mapping_path = "data/processed/station_mapping.csv"

ridership = pd.read_csv(ridership_path)
mapping = pd.read_csv(mapping_path)

print("Ridership rows:", len(ridership))
print("Mapping rows:", len(mapping))

ridership["station_complex_id"] = pd.to_numeric(
    ridership["station_complex_id"],
    errors="coerce"
)

mapping["complex_id"] = pd.to_numeric(
    mapping["complex_id"],
    errors="coerce"
)

merged = ridership.merge(
    mapping[
        [
            "complex_id",
            "gtfs_stop_id",
            "stop_name"
        ]
    ],
    left_on="station_complex_id",
    right_on="complex_id",
    how="left"
)

matched = merged["gtfs_stop_id"].notna().sum()
unmatched = merged["gtfs_stop_id"].isna().sum()

print("\nMatched rows:", matched)
print("Unmatched rows:", unmatched)

print("\nMatch percentage:")
print(round((matched / len(merged)) * 100, 2), "%")

print("\nSample:")
print(
    merged[
        [
            "transit_timestamp",
            "station_complex_id",
            "station_complex",
            "gtfs_stop_id",
            "stop_name",
            "passenger_entries"
        ]
    ].head(20)
)