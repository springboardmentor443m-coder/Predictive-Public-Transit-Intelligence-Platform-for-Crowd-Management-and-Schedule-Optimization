import pandas as pd

df = pd.read_csv(r"C:\Users\WaterMelon\OneDrive\Desktop\SpringBoard\MetroFlow\data\NYC_subway_traffic_2017-2021.csv")

df.drop_duplicates(inplace=True)

df["Datetime"] = pd.to_datetime(df["Datetime"])

df.to_csv(
    "data/cleaned_data.csv",
    index=False
)

df.drop(
    columns=[
        "North Direction Label",
        "South Direction Label"
    ],
    inplace=True
)