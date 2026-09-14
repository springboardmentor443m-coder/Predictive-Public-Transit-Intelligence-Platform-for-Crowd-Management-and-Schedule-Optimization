"""
Generate sample NYC Subway Traffic data for testing.
Creates a realistic dataset matching the Kaggle dataset structure.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def generate_sample_data(n_stations=469, n_days=365):
    """
    Generate sample NYC Subway Traffic data.
    This creates realistic data matching the Kaggle dataset structure.
    """
    print(f"Generating sample data for {n_stations} stations over {n_days} days...")
    
    # Generate date range (2017-01-01 to 2017-12-31)
    start_date = datetime(2017, 1, 1)
    dates = [start_date + timedelta(hours=i) for i in range(n_days * 24)]
    
    # Station names
    station_names = [f"Station_{i:03d}" for i in range(n_stations)]
    
    # Vectorized data generation
    np.random.seed(42)
    
    data = []
    for station_idx, station_name in enumerate(station_names):
        station_data = []
        for date in dates:
            hour = date.hour
            day_of_week = date.weekday()
            
            base_traffic = 1000 + 500 * np.sin((hour - 8) * np.pi / 12)
            if day_of_week < 5:
                base_traffic *= 1.5
                if 7 <= hour <= 9 or 17 <= hour <= 19:
                    base_traffic *= 2.0
            else:
                base_traffic *= 0.7
            
            entries = max(0, int(base_traffic + np.random.normal(0, 200)))
            exits = max(0, int(base_traffic * 0.8 + np.random.normal(0, 150)))
            
            station_data.append({
                'station_id': station_idx,
                'station_name': station_name,
                'datetime': date,
                'entries': entries,
                'exits': exits,
                'hour': hour,
                'day_of_week': day_of_week,
                'month': date.month,
                'is_weekend': 1 if day_of_week >= 5 else 0,
                'week_of_year': date.isocalendar()[1]
            })
        data.extend(station_data)
        if (station_idx + 1) % 100 == 0:
            print(f"  Generated {station_idx + 1}/{n_stations} stations...")
    
    df = pd.DataFrame(data)
    
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, "nyc_subway_traffic_2017_2021.csv")
    df.to_csv(filepath, index=False)
    print(f"Sample data saved to {filepath}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    return df

if __name__ == "__main__":
    df = generate_sample_data()
    print(f"\nFirst 5 rows:")
    print(df.head())
    print(f"\nStation count: {df['station_id'].nunique()}")
    print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
