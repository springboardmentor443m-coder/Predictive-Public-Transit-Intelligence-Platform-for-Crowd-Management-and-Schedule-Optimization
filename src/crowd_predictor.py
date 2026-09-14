import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBRegressor
import pickle
import os

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

class CrowdPredictor:
    """Machine learning model for predicting crowd levels at subway stations."""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = None
        self.is_trained = False
    
    def prepare_features(self, df):
        """Prepare features for the prediction model."""
        df = df.copy()
        
        # Create features
        feature_cols = []
        
        if 'datetime' in df.columns:
            df['hour'] = df['datetime'].dt.hour
            df['day_of_week'] = df['datetime'].dt.dayofweek
            df['month'] = df['datetime'].dt.month
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Categorical features
        cat_features = []
        if 'station_id' in df.columns:
            cat_features.append('station_id')
        if 'station_name' in df.columns:
            cat_features.append('station_name')
        if 'line_name' in df.columns:
            cat_features.append('line_name')
        
        # Encode categorical features
        for col in cat_features:
            le = LabelEncoder()
            df[f'{col}_encoded'] = le.fit_transform(df[col].astype(str))
            self.label_encoders[col] = le
        
        # Select numeric features
        numeric_features = [c for c in df.select_dtypes(include=[np.number]).columns 
                           if c not in cat_features]
        
        # Remove target columns if present
        target_cols = ['entries', 'entries_hourly', 'exit_hourly']
        numeric_features = [c for c in numeric_features if c not in target_cols]
        
        self.feature_names = numeric_features
        X = df[numeric_features].fillna(0)
        
        return X
    
    def find_target_column(self, df):
        """Find the target column in the dataset."""
        potential_targets = ['entries', 'entries_hourly', 'entry_hourly', 'exit_hourly', 
                           'total_entries', 'Total Entries', 'ENTRIES']
        for col in potential_targets:
            if col in df.columns:
                return col
        
        # Return first numeric column that isn't a date-related feature
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in ['hour', 'day_of_week', 'month', 'is_weekend', 'week_of_year']:
                return col
        
        return numeric_cols[0] if len(numeric_cols) > 0 else None
    
    def train(self, df, test_size=0.2):
        """Train the crowd prediction model."""
        X = self.prepare_features(df)
        target_col = self.find_target_column(df)
        y = df[target_col].fillna(0)
        
        # Drop rows with NaN targets
        valid_idx = y.dropna().index
        X = X.loc[valid_idx]
        y = y.loc[valid_idx]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Try multiple models and pick the best
        models = {
            'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
            'GradientBoosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'XGBoost': XGBRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        }
        
        best_model = None
        best_score = float('-inf')
        best_name = ''
        
        for name, model in models.items():
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            score = r2_score(y_test, y_pred)
            print(f"{name} R² Score: {score:.4f}")
            
            if score > best_score:
                best_score = score
                best_model = model
                best_name = name
        
        self.model = best_model
        self.is_trained = True
        print(f"\nBest model: {best_name} with R² = {best_score:.4f}")
        
        # Store feature names and scaler
        self.feature_names = list(X.columns)
        
        return {
            'model_name': best_name,
            'r2_score': best_score,
            'mae': mean_absolute_error(y_test, self.model.predict(X_test_scaled)),
            'rmse': np.sqrt(mean_squared_error(y_test, self.model.predict(X_test_scaled)))
        }
    
    def predict(self, df):
        """Make predictions on new data."""
        if not self.is_trained:
            raise ValueError("Model has not been trained yet. Call train() first.")
        
        X = self.prepare_features(df)
        # Ensure same feature columns
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0
        X = X[self.feature_names]
        X_scaled = self.scaler.transform(X.fillna(0))
        
        predictions = self.model.predict(X_scaled)
        return predictions
    
    def predict_weekly_schedule(self, stations_df):
        """Generate predictions for a weekly schedule."""
        if not self.is_trained:
            raise ValueError("Model has not been trained yet.")
        
        predictions = self.predict(stations_df)
        stations_df['predicted_traffic'] = predictions
        return stations_df
    
    def save_model(self, filepath=None):
        """Save the trained model to disk."""
        os.makedirs(MODELS_DIR, exist_ok=True)
        if filepath is None:
            filepath = os.path.join(MODELS_DIR, 'crowd_predictor_model.pkl')
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath=None):
        """Load a trained model from disk."""
        if filepath is None:
            filepath = os.path.join(MODELS_DIR, 'crowd_predictor_model.pkl')
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoders = model_data['label_encoders']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']
        
        print(f"Model loaded from {filepath}")
