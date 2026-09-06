import os
import sys
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = os.path.join(
    "models",
    "historical_delay_target.csv"
)

MODEL_DIR = "models"

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "delay_prediction_model.joblib"
)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("V/LINE DELAY PREDICTION MODEL")
    print("=" * 60)

    # --------------------------------------------------------
    # Check target dataset
    # --------------------------------------------------------

    print("\nChecking historical delay target dataset...")

    if not os.path.exists(INPUT_FILE):

        print("\nMODEL TRAINING CANNOT START")
        print("-" * 60)

        print(
            f"\nRequired file not found:\n"
            f"{INPUT_FILE}"
        )

        print(
            "\nThis is expected while genuine historical "
            "delay observations are unavailable."
        )

        print(
            "\nThe model will NOT be trained using:"
            "\n  - artificial delay values"
            "\n  - scheduled travel time as delay"
            "\n  - fabricated labels"
        )

        print(
            "\nModel status: WAITING FOR REAL DELAY DATA"
        )

        sys.exit(0)

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    df = pd.read_csv(INPUT_FILE)

    print(f"\nRows loaded: {len(df)}")
    print(f"Columns loaded: {len(df.columns)}")

    TARGET = "delay_seconds"

    if TARGET not in df.columns:

        print(
            f"\nERROR: Required target column "
            f"'{TARGET}' is missing."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Validate target
    # --------------------------------------------------------

    df[TARGET] = pd.to_numeric(
        df[TARGET],
        errors="coerce"
    )

    df = df.dropna(
        subset=[TARGET]
    )

    print(
        f"\nValid delay observations: {len(df)}"
    )

    if len(df) < 20:

        print(
            "\nNot enough genuine observations "
            "to train the model safely."
        )

        sys.exit(0)

    # --------------------------------------------------------
    # Remove target from features
    # --------------------------------------------------------

    X = df.drop(
        columns=[TARGET]
    )

    y = df[TARGET]

    # --------------------------------------------------------
    # Select useful feature types
    # --------------------------------------------------------

    numeric_features = [
        column
        for column in X.columns
        if pd.api.types.is_numeric_dtype(X[column])
    ]

    categorical_features = [
        column
        for column in X.columns
        if column not in numeric_features
    ]

    # --------------------------------------------------------
    # Preprocessing
    # --------------------------------------------------------

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                )
            )
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                )
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore"
                )
            )
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                numeric_features
            ),
            (
                "categorical",
                categorical_pipeline,
                categorical_features
            )
        ]
    )

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor
            ),
            (
                "model",
                model
            )
        ]
    )

    # --------------------------------------------------------
    # Train/test split
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42
    )

    print(
        f"\nTraining observations: {len(X_train)}"
    )

    print(
        f"Testing observations: {len(X_test)}"
    )

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    print("\nTraining Random Forest delay model...")

    pipeline.fit(
        X_train,
        y_train
    )

    # --------------------------------------------------------
    # Evaluate
    # --------------------------------------------------------

    predictions = pipeline.predict(
        X_test
    )

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    mse = mean_squared_error(
        y_test,
        predictions
    )

    rmse = mse ** 0.5

    r2 = r2_score(
        y_test,
        predictions
    )

    print("\n" + "=" * 60)
    print("MODEL EVALUATION")
    print("=" * 60)

    print(
        f"\nMAE : {mae:.2f} seconds"
    )

    print(
        f"RMSE: {rmse:.2f} seconds"
    )

    print(
        f"R²  : {r2:.4f}"
    )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    joblib.dump(
        pipeline,
        MODEL_FILE
    )

    print(
        "\nSaved trained model to:"
    )

    print(
        MODEL_FILE
    )

    print(
        "\nV/Line delay prediction model "
        "completed successfully!"
    )


if __name__ == "__main__":
    main()