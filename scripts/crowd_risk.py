"""
MetroFlow Phase 2: Crowd Risk Engine
====================================
Derives station-level historical demand percentiles (50th, 80th, 95th) from training data,
classifies predicted next-hour demand into 4 crowd risk levels (LOW, MODERATE, HIGH, CRITICAL),
and assigns operational recommendation actions.

Outputs:
  - metroflow/data/processed/metroflow_predictions.csv
  - metroflow/data/processed/station_risk_thresholds.csv
"""

import os
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

FEATURES_DF_CSV = os.path.join(PROCESSED_DIR, "metroflow_features_df.csv")
PREDICTIONS_CSV = os.path.join(PROCESSED_DIR, "metroflow_predictions.csv")
THRESHOLDS_CSV = os.path.join(PROCESSED_DIR, "station_risk_thresholds.csv")

def log(msg):
    print(msg, flush=True)

def compute_risk_thresholds(df):
    """Computes 50th, 80th, and 95th percentiles of historical passenger demand per station complex."""
    log("[CROWD RISK ENGINE] Computing station-level historical demand percentiles...")
    thresholds = {}
    records = []
    
    for st_id, group in df.groupby('station_complex_id'):
        p50 = group['passenger_count'].quantile(0.50)
        p80 = group['passenger_count'].quantile(0.80)
        p95 = group['passenger_count'].quantile(0.95)
        st_name = group['station_complex'].iloc[0]
        
        thresholds[st_id] = {'p50': p50, 'p80': p80, 'p95': p95}
        records.append({
            'station_complex_id': st_id,
            'station_complex': st_name,
            'p50_low_threshold': p50,
            'p80_moderate_threshold': p80,
            'p95_high_threshold': p95
        })
        
    df_thresh = pd.DataFrame(records)
    df_thresh.to_csv(THRESHOLDS_CSV, index=False)
    log(f"[SAVED] {THRESHOLDS_CSV}")
    return thresholds, df_thresh

def classify_crowd_risk(row, thresholds):
    """Classifies predicted next-hour demand into LOW, MODERATE, HIGH, CRITICAL."""
    st_id = row['station_complex_id']
    pred = row['predicted_next_hour']
    
    thresh = thresholds.get(st_id, {'p50': 1000, 'p80': 2500, 'p95': 4000})
    
    if pred < thresh['p50']:
        risk = "LOW"
        action = "Normal monitoring"
    elif pred < thresh['p80']:
        risk = "MODERATE"
        action = "Monitor station demand"
    elif pred < thresh['p95']:
        risk = "HIGH"
        action = "Increase monitoring + prepare additional service"
    else:
        risk = "CRITICAL"
        action = "Increase train frequency + deploy crowd control measures"
        
    return risk, action

def run_crowd_risk_engine():
    log("=" * 60)
    log("STARTING METROFLOW CROWD RISK CLASSIFICATION ENGINE")
    log("=" * 60)
    
    if not os.path.exists(FEATURES_DF_CSV):
        raise FileNotFoundError(f"Feature matrix file not found at {FEATURES_DF_CSV}. Run train_demand_model.py first.")
        
    log(f"[DATA] Loading predictions matrix from {FEATURES_DF_CSV}...")
    df = pd.read_csv(FEATURES_DF_CSV)
    df['station_complex_id'] = df['station_complex_id'].astype(str)
    
    # Compute station risk thresholds
    thresholds, df_thresh = compute_risk_thresholds(df)
    
    log("[CROWD RISK ENGINE] Classifying predicted demand and assigning recommendations...")
    risk_action_tuples = [classify_crowd_risk(row, thresholds) for _, row in df.iterrows()]
    
    df['crowd_risk'] = [t[0] for t in risk_action_tuples]
    df['recommended_action'] = [t[1] for t in risk_action_tuples]
    
    # Select required columns
    required_cols = [
        'transit_timestamp',
        'station_complex_id',
        'station_complex',
        'passenger_count',
        'target_next_hour',
        'predicted_next_hour',
        'absolute_error',
        'crowd_risk',
        'recommended_action'
    ]
    
    df_predictions = df[required_cols].copy()
    
    df_predictions.to_csv(PREDICTIONS_CSV, index=False)
    log(f"[SAVED] {PREDICTIONS_CSV}")
    
    # Validation & Statistics
    log("\n" + "=" * 40)
    log("CROWD RISK DISTRIBUTION SUMMARY")
    log("=" * 40)
    risk_counts = df_predictions['crowd_risk'].value_counts()
    risk_pcts = df_predictions['crowd_risk'].value_counts(normalize=True) * 100
    
    dist_df = pd.DataFrame({
        'count': risk_counts,
        'percentage': risk_pcts.map("{:.2f}%".format)
    })
    log(dist_df.to_string())
    
    # Assertions
    unique_risks = set(df_predictions['crowd_risk'].unique())
    expected_risks = {'LOW', 'MODERATE', 'HIGH', 'CRITICAL'}
    assert expected_risks.issubset(unique_risks), f"Missing risk categories! Expected all 4, got: {unique_risks}"
    
    log("\n--- SAMPLE PREDICTIONS WITH RISK LABELS ---")
    log(df_predictions.head(10).to_string(index=False))
    
    log("\n========================================")
    log("CROWD RISK ENGINE COMPLETE (PASS)")
    log("========================================")

if __name__ == "__main__":
    run_crowd_risk_engine()
