"""
Test evaluation of R2 and RMSE across depths on test set with 10 trees
"""
import time
import polars as pl
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

print("Loading train and test parquet...")
train_df = pl.read_parquet(r"eval\train_6m.parquet")
test_df = pl.read_parquet(r"eval\test_6m.parquet")

X_train = train_df.drop("total_flow").to_numpy()
y_train = train_df["total_flow"].to_numpy()

X_test = test_df.drop("total_flow").to_numpy()
y_test = test_df["total_flow"].to_numpy()

print(f"Train shape: {X_train.shape}, Test shape: {X_test.shape}")

for depth in [10, 15, 20]:
    t0 = time.time()
    rf = RandomForestRegressor(
        n_estimators=10,
        max_depth=depth,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=42
    )
    rf.fit(X_train, y_train)
    fit_time = time.time() - t0
    
    t_pred = time.time()
    y_pred = rf.predict(X_test)
    pred_time = time.time() - t_pred
    
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    
    print(f"Depth {depth:2d} (10 trees): fit={fit_time:.1f}s, pred={pred_time:.1f}s | Test R2={r2:.4f}, RMSE={rmse:.2f}, MAE={mae:.2f}")
