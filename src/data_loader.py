import pandas as pd
import numpy as np
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def download_kaggle_dataset():
    """Download NYC Subway Traffic dataset from Kaggle."""
    os.system("kaggle datasets download -d eddeng/nyc-subway-traffic-data-20172021 -p data/")
    os.system("cd data && unzip -o nyc-subway-traffic-data-20172021.zip && cd ..")
    print("Dataset downloaded and extracted.")

def load_data(filepath=None):
    """Load and validate the NYC Subway Traffic dataset."""
    if filepath is None:
        filepath = os.path.join(DATA_DIR, "nyc_subway_traffic_2017_2021.csv")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at {filepath}. Run download_kaggle_dataset() first.")
    
    df = pd.read_csv(filepath)
    print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Columns: {df.columns.tolist()}")
    return df

def preprocess_data(df):
    """Preprocess the subway traffic data."""
    df = df.copy()
    
    # Convert date columns
    date_cols = [c for c in df.columns if 'date' in c.lower() or c == 'day']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Handle missing values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    # Add derived features
    if 'datetime' in df.columns or 'date' in df.columns:
        time_col = 'datetime' if 'datetime' in df.columns else 'date'
        df['hour'] = df[time_col].dt.hour
        df['day_of_week'] = df[time_col].dt.dayofweek
        df['day_of_month'] = df[time_col].dt.day
        df['month'] = df[time_col].dt.month
        df['week_of_year'] = df[time_col].dt.isocalendar().week.astype(int)
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    print("Data preprocessing complete.")
    return df

def filter_station(df, station_name=None, station_id=None):
    """Filter data for a specific station."""
    if station_name:
        station_col = 'station_name' if 'station_name' in df.columns else df.columns[0]
        df = df[df[station_col] == station_name]
    return df

def aggregate_hourly(df):
    """Aggregate data to hourly level."""
    if 'hour' in df.columns and 'station_id' in df.columns:
        hourly = df.groupby(['station_id', 'datetime', 'hour']).sum().reset_index()
    else:
        hourly = df.groupby('datetime').sum().reset_index()
    return hourly

def aggregate_weekly(df):
    """Aggregate data to weekly level for schedule analysis."""
    if 'week_of_year' in df.columns:
        weekly = df.groupby(['station_id', 'week_of_year', 'day_of_week']).agg({
            col: 'sum' for col in df.select_dtypes(include=[np.number]).columns if col not in ['week_of_year', 'day_of_week']
        }).reset_index()
    else:
        df['week_of_year'] = df['datetime'].dt.isocalendar().week.astype(int)
        df['day_of_week'] = df['datetime'].dt.dayofweek
        weekly = df.groupby(['week_of_year', 'day_of_week']).agg({
            col: 'sum' for col in df.select_dtypes(include=[np.number]).columns
        }).reset_index()
    return weekly
