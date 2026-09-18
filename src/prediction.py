"""
AI MetroFlow - Real-Time Congestion Prediction & Recommendation Engine
Loads the trained model artifact and provides single and batch inference
with confidence probability scores and actionable operational recommendations.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Union, Optional

import numpy as np
import pandas as pd

# Ensure local package imports work reliably
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils import (
    load_model_bundle,
    get_congestion_recommendation,
    DEFAULT_MODEL_PATH,
)

logger = logging.getLogger("MetroFlow.Prediction")


class CongestionPredictor:
    """
    Production-ready inference engine for NYC subway crowd level prediction.
    """

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        """Initializes the predictor by loading the saved model bundle."""
        logger.info("Initializing CongestionPredictor from: %s", model_path)
        self.bundle = load_model_bundle(model_path)
        self.model = self.bundle["model"]
        self.model_name = self.bundle.get("model_name", "Classifier")
        self.encoders = self.bundle["encoders"]
        self.target_encoder = self.bundle.get("target_encoder")
        self.feature_cols = self.bundle["feature_cols"]
        self.target_classes = self.bundle.get("target_classes", ["High", "Low", "Medium"])
        logger.info(
            "Predictor ready. Model: %s, Features: %d, Classes: %s",
            self.model_name,
            len(self.feature_cols),
            self.target_classes,
        )

    def _prepare_input_df(self, raw_data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame]) -> pd.DataFrame:
        """
        Normalizes and prepares raw inputs, encoding categoricals and imputing derived features.
        """
        if isinstance(raw_data, dict):
            df = pd.DataFrame([raw_data])
        elif isinstance(raw_data, list):
            df = pd.DataFrame(raw_data)
        elif isinstance(raw_data, pd.DataFrame):
            df = raw_data.copy()
        else:
            raise TypeError(f"Unsupported input data type: {type(raw_data)}")

        # Automatically derive missing temporal flags if base temporal features exist
        if "is_weekend" not in df.columns:
            if "day_of_week" in df.columns:
                df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
            else:
                df["is_weekend"] = 0

        if "is_peak_hour" not in df.columns:
            if "hour" in df.columns:
                df["is_peak_hour"] = df["hour"].isin([7, 8, 9, 16, 17, 18, 19]).astype(int)
            else:
                df["is_peak_hour"] = 0

        # Fill default date parts if missing
        if "day" not in df.columns:
            df["day"] = 15
        if "month" not in df.columns:
            df["month"] = 6
        if "year" not in df.columns:
            df["year"] = 2021
        if "day_of_week" not in df.columns:
            df["day_of_week"] = 2  # Wednesday default

        # Default coordinates for Manhattan center if missing
        if "Latitude" not in df.columns:
            df["Latitude"] = 40.7580
        if "Longitude" not in df.columns:
            df["Longitude"] = -73.9855

        # Encode categorical columns using saved LabelEncoders
        categorical_mappings = {
            "Borough": "borough_encoded",
            "Structure": "structure_encoded",
            "Stop Name": "station_encoded",
        }

        for cat_col, enc_col in categorical_mappings.items():
            # Check either the feature column name or standard encoded name
            target_col = None
            if enc_col in self.feature_cols:
                target_col = enc_col
            elif f"{cat_col}_encoded" in self.feature_cols:
                target_col = f"{cat_col}_encoded"

            if target_col and cat_col in self.encoders:
                le = self.encoders[cat_col]
                known = set(le.classes_)
                if cat_col in df.columns:
                    safe_series = df[cat_col].astype(str).map(lambda x: x if x in known else le.classes_[0])
                    df[target_col] = le.transform(safe_series)
                else:
                    df[target_col] = 0

        # Verify all feature columns are present
        for col in self.feature_cols:
            if col not in df.columns:
                df[col] = 0

        return df[self.feature_cols]

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes single-instance prediction.
        
        Args:
            input_data: Dictionary containing transit features.
            
        Returns:
            Dictionary matching the required specification:
            {
                "congestion_level": "High",
                "confidence": 0.94,
                "recommendation": "..."
            }
        """
        X = self._prepare_input_df(input_data)
        
        # Predict class and probabilities
        if self.target_encoder is not None:
            # XGBoost encoded pipeline
            pred_idx = self.model.predict(X)[0]
            pred_label = self.target_encoder.inverse_transform([pred_idx])[0]
            probs = self.model.predict_proba(X)[0]
            confidence = float(probs[pred_idx])
            prob_dict = {
                cls: round(float(probs[i]), 4)
                for i, cls in enumerate(self.target_encoder.classes_)
            }
        else:
            # Standard Scikit-Learn (Random Forest / Decision Tree)
            pred_label = str(self.model.predict(X)[0])
            probs = self.model.predict_proba(X)[0]
            class_indices = {cls: idx for idx, cls in enumerate(self.model.classes_)}
            confidence = float(probs[class_indices[pred_label]])
            prob_dict = {
                cls: round(float(probs[class_indices[cls]]), 4)
                for cls in self.model.classes_
            }

        recommendation = get_congestion_recommendation(pred_label, confidence)

        return {
            "congestion_level": pred_label,
            "confidence": round(confidence, 4),
            "recommendation": recommendation,
            "probabilities": prob_dict,
        }

    def predict_batch(self, data: Union[List[Dict[str, Any]], pd.DataFrame]) -> pd.DataFrame:
        """
        Executes high-throughput batch prediction.
        
        Args:
            data: List of feature dictionaries or pandas DataFrame.
            
        Returns:
            DataFrame with predictions, confidence scores, and recommendations.
        """
        if isinstance(data, list):
            df_in = pd.DataFrame(data)
        else:
            df_in = data.copy()

        X = self._prepare_input_df(df_in)

        if self.target_encoder is not None:
            pred_indices = self.model.predict(X)
            pred_labels = self.target_encoder.inverse_transform(pred_indices)
            probs = self.model.predict_proba(X)
            confidences = [float(probs[i, idx]) for i, idx in enumerate(pred_indices)]
        else:
            pred_labels = self.model.predict(X)
            probs = self.model.predict_proba(X)
            class_map = {cls: idx for idx, cls in enumerate(self.model.classes_)}
            confidences = [float(probs[i, class_map[label]]) for i, label in enumerate(pred_labels)]

        df_out = df_in.copy()
        df_out["predicted_congestion"] = pred_labels
        df_out["confidence"] = [round(c, 4) for c in confidences]
        df_out["recommendation"] = [get_congestion_recommendation(lbl, c) for lbl, c in zip(pred_labels, confidences)]

        return df_out


def main():
    """CLI demonstration of real-time subway crowd prediction."""
    print("=" * 70)
    print("AI METROFLOW - CONGESTION PREDICTION & RECOMMENDATION ENGINE")
    print("=" * 70)

    try:
        predictor = CongestionPredictor()
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Please train the model first by running: python src/train_model.py")
        sys.exit(1)

    # Scenario 1: Peak Rush Hour at Grand Central - 42 St
    scenario_rush = {
        "Stop Name": "Grand Central - 42 St",
        "Borough": "M",
        "Structure": "Subway",
        "Latitude": 40.751776,
        "Longitude": -73.976848,
        "hour": 8,
        "day": 12,
        "month": 10,
        "year": 2021,
        "day_of_week": 2,  # Tuesday
    }

    # Scenario 2: Late Night Weekend at an Outer Borough Station
    scenario_offpeak = {
        "Stop Name": "111 St",
        "Borough": "Q",
        "Structure": "Elevated",
        "Latitude": 40.684331,
        "Longitude": -73.832163,
        "hour": 2,
        "day": 17,
        "month": 10,
        "year": 2021,
        "day_of_week": 6,  # Sunday
    }

    print("\n--- Scenario 1: Grand Central Terminal (Tuesday 8:00 AM Rush Hour) ---")
    result_rush = predictor.predict(scenario_rush)
    print(json.dumps({
        "congestion_level": result_rush["congestion_level"],
        "confidence": result_rush["confidence"],
        "recommendation": result_rush["recommendation"]
    }, indent=2))
    print(f"Class Probabilities: {result_rush['probabilities']}")

    print("\n--- Scenario 2: Outer Queens Elevated (Sunday 2:00 AM Off-Peak) ---")
    result_offpeak = predictor.predict(scenario_offpeak)
    print(json.dumps({
        "congestion_level": result_offpeak["congestion_level"],
        "confidence": result_offpeak["confidence"],
        "recommendation": result_offpeak["recommendation"]
    }, indent=2))
    print(f"Class Probabilities: {result_offpeak['probabilities']}")

    # Batch Prediction Demonstration
    print("\n--- Batch Prediction Demonstration (3 Stations) ---")
    batch_data = [
        scenario_rush,
        scenario_offpeak,
        {
            "Stop Name": "14 St - Union Sq",
            "Borough": "M",
            "Structure": "Subway",
            "Latitude": 40.735736,
            "Longitude": -73.990568,
            "hour": 17,
            "day": 15,
            "month": 5,
            "year": 2021,
            "day_of_week": 4,  # Friday 5 PM
        },
    ]
    batch_results = predictor.predict_batch(batch_data)
    cols_to_show = ["Stop Name", "hour", "day_of_week", "predicted_congestion", "confidence"]
    print(batch_results[cols_to_show].to_string(index=False))
    print("=" * 70)


if __name__ == "__main__":
    main()
