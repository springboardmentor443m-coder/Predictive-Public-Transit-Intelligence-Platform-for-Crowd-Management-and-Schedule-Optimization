import pandas as pd

input_path = "data/processed/station_mapping.csv"

df = pd.read_csv(input_path)

print("Total mapping rows:", len(df))

stops_per_complex = (
    df.groupby("complex_id")["gtfs_stop_id"]
    .nunique()
    .reset_index(name="gtfs_stop_count")
)

print("\nGTFS stops per complex:")
print(stops_per_complex["gtfs_stop_count"].value_counts().sort_index())

print("\nComplexes with multiple GTFS stops:")
print(
    stops_per_complex[
        stops_per_complex["gtfs_stop_count"] > 1
    ].head(30)
)

print("\nMaximum GTFS stops in one complex:")
print(stops_per_complex["gtfs_stop_count"].max())
