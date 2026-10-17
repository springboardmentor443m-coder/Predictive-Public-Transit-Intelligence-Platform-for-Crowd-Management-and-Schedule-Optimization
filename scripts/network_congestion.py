"""
MetroFlow Phase 3: Connected-Station Congestion & Propagation Engine
======================================================================
Calculates topological graph network features, estimates connected-station congestion pressure,
and generates explainable operational recommendations.

Outputs:
  - metroflow/data/processed/network_features.csv
  - metroflow/data/processed/network_congestion_predictions.csv
  - metroflow/data/processed/network_congestion_model.pkl
  - metroflow/data/processed/network_model_features.json
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

NETWORK_JSON = os.path.join(DATA_DIR, "station_network.json")
PREDICTIONS_CSV = os.path.join(PROCESSED_DIR, "metroflow_predictions.csv")
MASTER_CSV = os.path.join(PROCESSED_DIR, "metroflow_master.csv")

NETWORK_FEATURES_CSV = os.path.join(PROCESSED_DIR, "network_features.csv")
NETWORK_PREDICTIONS_CSV = os.path.join(PROCESSED_DIR, "network_congestion_predictions.csv")
MODEL_PKL = os.path.join(PROCESSED_DIR, "network_congestion_model.pkl")
FEATURES_JSON = os.path.join(PROCESSED_DIR, "network_model_features.json")

def log(msg):
    print(msg, flush=True)

def load_station_network():
    """Loads topological station graph network."""
    if not os.path.exists(NETWORK_JSON):
        raise FileNotFoundError(f"Station network file not found at {NETWORK_JSON}")
    with open(NETWORK_JSON, 'r') as f:
        data = json.load(f)
    nodes = {n['complex_id']: n for n in data['nodes']}
    return nodes

def build_network_features():
    """Builds topological graph features per station timestamp."""
    log("[NETWORK CONGESTION ENGINE] Loading predictions & network graph...")
    
    nodes = load_station_network()
    
    if not os.path.exists(PREDICTIONS_CSV):
        raise FileNotFoundError(f"Predictions file not found at {PREDICTIONS_CSV}")
        
    df = pd.read_csv(PREDICTIONS_CSV)
    df['station_complex_id'] = df['station_complex_id'].astype(str)
    df['transit_timestamp'] = pd.to_datetime(df['transit_timestamp'])
    
    # Calculate neighbor metrics
    log("[NETWORK CONGESTION ENGINE] Computing connected station lag & propagation pressure...")
    
    # Map predictions by timestamp and station
    lookup = df.set_index(['transit_timestamp', 'station_complex_id'])['predicted_next_hour'].to_dict()
    
    neighbor_means = []
    station_degrees = []
    transfer_hubs = []
    
    for idx, row in df.iterrows():
        st_id = row['station_complex_id']
        ts = row['transit_timestamp']
        node = nodes.get(st_id, {})
        
        neighbors = node.get('neighbors', [])
        degrees = len(neighbors)
        is_hub = 1 if node.get('transfer_hub', False) else 0
        
        station_degrees.append(degrees)
        transfer_hubs.append(is_hub)
        
        # Calculate mean predicted demand of neighbors at current timestamp
        vals = [lookup.get((ts, n_id), 0.0) for n_id in neighbors if (ts, n_id) in lookup]
        mean_neighbor_pred = np.mean(vals) if vals else row['predicted_next_hour']
        neighbor_means.append(mean_neighbor_pred)
        
    df['station_degree'] = station_degrees
    df['is_transfer_hub'] = transfer_hubs
    df['neighbor_predicted_demand'] = neighbor_means
    df['network_pressure_ratio'] = df['neighbor_predicted_demand'] / (df['predicted_next_hour'] + 1.0)
    
    # Calculate Network Risk & Explainable Factors
    log("[NETWORK CONGESTION ENGINE] Classifying network congestion risk and generating explainable factors...")
    
    network_risks = []
    contributing_factors_list = []
    recommended_actions_list = []
    
    for idx, row in df.iterrows():
        st_name = row['station_complex']
        base_risk = row['crowd_risk']
        net_ratio = row['network_pressure_ratio']
        neighbor_demand = row['neighbor_predicted_demand']
        
        factors = []
        if base_risk in ['HIGH', 'CRITICAL']:
            factors.append(f"Elevated primary station demand forecast ({int(row['predicted_next_hour']):,} passengers)")
        if net_ratio > 1.2:
            factors.append(f"Connected neighbor demand exceeds local baseline by {int((net_ratio-1)*100)}%")
        if neighbor_demand > 3000:
            factors.append(f"High adjacent hub volume ({int(neighbor_demand):,} avg neighbor demand)")
        if row['is_transfer_hub']:
            factors.append("Multi-line transfer hub bottleneck risk")
            
        if not factors:
            factors.append("Normal station flow across connected network")
            
        # Determine Network Risk Tier
        if base_risk == 'CRITICAL' or (base_risk == 'HIGH' and net_ratio > 1.15):
            net_risk = 'CRITICAL'
            action = "Deploy platform crowd management staff + issue advisory to adjust train dwell times"
        elif base_risk == 'HIGH' or net_ratio > 1.25:
            net_risk = 'HIGH'
            action = "Increase platform monitoring + prepare service frequency adjustments on connected lines"
        elif base_risk == 'MODERATE' or net_ratio > 1.05:
            net_risk = 'MODERATE'
            action = "Monitor station and adjacent hub passenger entry rates"
        else:
            net_risk = 'LOW'
            action = "Normal network monitoring"
            
        network_risks.append(net_risk)
        contributing_factors_list.append(" | ".join(factors))
        recommended_actions_list.append(action)
        
    df['network_risk'] = network_risks
    df['contributing_factors'] = contributing_factors_list
    df['recommended_action'] = recommended_actions_list
    
    df.to_csv(NETWORK_FEATURES_CSV, index=False)
    df.to_csv(NETWORK_PREDICTIONS_CSV, index=False)
    log(f"[SAVED] {NETWORK_FEATURES_CSV}")
    log(f"[SAVED] {NETWORK_PREDICTIONS_CSV}")
    
    return df

def train_network_congestion_model(df):
    """Trains a classifier predicting network risk level."""
    log("\n[TRAINING] Fitting RandomForestClassifier for Network Congestion Risk...")
    
    feature_cols = [
        'predicted_next_hour', 'station_degree', 'is_transfer_hub',
        'neighbor_predicted_demand', 'network_pressure_ratio'
    ]
    
    # Map target risk
    risk_map = {'LOW': 0, 'MODERATE': 1, 'HIGH': 2, 'CRITICAL': 3}
    df['network_risk_code'] = df['network_risk'].map(risk_map)
    
    df_sorted = df.sort_values(by='transit_timestamp').reset_index(drop=True)
    split_idx = int(len(df_sorted) * 0.8)
    
    train_df = df_sorted.iloc[:split_idx]
    test_df = df_sorted.iloc[split_idx:]
    
    X_train, y_train = train_df[feature_cols], train_df['network_risk_code']
    X_test, y_test = test_df[feature_cols], test_df['network_risk_code']
    
    model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
    rec = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))
    f1 = float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
    
    log("=" * 40)
    log("NETWORK CONGESTION MODEL METRICS")
    log("=" * 40)
    log(f"Accuracy:  {acc:.4f}")
    log(f"Precision: {prec:.4f}")
    log(f"Recall:    {rec:.4f}")
    log(f"F1 Score:  {f1:.4f}")
    
    joblib.dump(model, MODEL_PKL)
    log(f"[SAVED] {MODEL_PKL}")
    
    with open(FEATURES_JSON, 'w') as f:
        json.dump(feature_cols, f, indent=2)
    log(f"[SAVED] {FEATURES_JSON}")

def run_pipeline():
    log("=" * 60)
    log("STARTING METROFLOW NETWORK CONGESTION & PROPAGATION ENGINE")
    log("=" * 60)
    df = build_network_features()
    train_network_congestion_model(df)
    log("=" * 60)
    log("NETWORK CONGESTION PIPELINE COMPLETE")
    log("=" * 60)

if __name__ == "__main__":
    run_pipeline()
