"""
Predictive Public Transit Intelligence Platform for Crowd Management and Schedule Optimization
Using NYC Subway Traffic 2017-21 Dataset
Main Pipeline Entry Point
"""

import os
import sys
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_data, preprocess_data, download_kaggle_dataset
from src.eda import generate_eda_report
from src.weekly_analysis import WeeklyScheduleAnalyzer
from src.crowd_predictor import CrowdPredictor
from src.schedule_optimizer import ScheduleOptimizer
from src.visualization import create_all_visualizations

def main():
    """Run the complete pipeline."""
    print("=" * 70)
    print("PREDICTIVE PUBLIC TRANSIT INTELLIGENCE PLATFORM")
    print("NYC Subway Traffic 2017-21 | Crowd Management & Schedule Optimization")
    print("=" * 70)
    
    # Step 1: Load Data
    print("\n[Step 1] Loading NYC Subway Traffic Dataset...")
    try:
        df = load_data()
    except FileNotFoundError:
        print("Dataset not found. Attempting to download from Kaggle...")
        download_kaggle_dataset()
        df = load_data()
    
    # Step 2: Preprocess
    print("\n[Step 2] Preprocessing Data...")
    df = preprocess_data(df)
    
    # Step 3: EDA
    print("\n[Step 3] Running Exploratory Data Analysis...")
    generate_eda_report(df)
    
    # Sample data for heavier computations
    if len(df) > 100000:
        print(f"\nSampling {len(df)} rows to ~100000 for faster processing...")
        station_ids = df['station_id'].unique()
        sample_per = min(300, len(df) // len(station_ids))
        df_sample = pd.concat([g.sample(sample_per) for _, g in df.groupby('station_id')])
        print(f"Sample size: {len(df_sample)} rows")
    else:
        df_sample = df
    
    # Step 4: Weekly Analysis
    print("\n[Step 4] Analyzing Weekly Patterns...")
    weekly_analyzer = WeeklyScheduleAnalyzer(df_sample)
    weekly_report = weekly_analyzer.generate_weekly_report()
    
    # Step 5: Crowd Prediction
    print("\n[Step 5] Training Crowd Prediction Model...")
    predictor = CrowdPredictor()
    model_results = predictor.train(df_sample)
    predictor.save_model()
    
    # Step 6: Schedule Optimization
    print("\n[Step 6] Optimizing Schedules...")
    optimizer = ScheduleOptimizer(df_sample)
    schedule_report = optimizer.generate_schedule_report()
    optimizer.save_schedule()
    
    # Step 7: Visualizations
    print("\n[Step 7] Generating Visualizations...")
    create_all_visualizations(df_sample)
    
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE!")
    print("=" * 70)
    print(f"\nResults saved to:")
    print(f"  - Models: models/")
    print(f"  - Visualizations: visualizations/")
    print(f"  - Reports: reports/")
    print(f"\nModel Performance: R² = {model_results['r2_score']:.4f}")

if __name__ == "__main__":
    main()
