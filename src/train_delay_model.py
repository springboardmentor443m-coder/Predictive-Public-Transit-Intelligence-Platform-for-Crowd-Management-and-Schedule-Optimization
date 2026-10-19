import os
import sys
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = os.path.join(
    "data",
    "realtime",
    "historical_delay_features.csv"
)

OUTPUT_DIR = os.path.join("models")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 50)
    print("DELAY MODEL TRAINING PREPARATION")
    print("=" * 50)

    # --------------------------------------------------------
    # Check input file
    # --------------------------------------------------------

    print("\nLoading historical delay features...")

    if not os.path.exists(INPUT_FILE):
        print(f"\nERROR: Input file not found:")
        print(INPUT_FILE)
        sys.exit(1)

    df = pd.read_csv(INPUT_FILE)

    print(f"Rows loaded: {len(df)}")
    print(f"Columns loaded: {len(df.columns)}")

    # --------------------------------------------------------
    # Display columns
    # --------------------------------------------------------

    print("\nAvailable columns:")

    for column in df.columns:
        print(f"  {column}")

    # --------------------------------------------------------
    # Check required target
    # --------------------------------------------------------

    TARGET_COLUMN = "delay_seconds"

    print("\nChecking model target...")

    if TARGET_COLUMN not in df.columns:

        print("\n" + "=" * 50)
        print("MODEL TRAINING CANNOT START YET")
        print("=" * 50)

        print(
            f"\nRequired target column '{TARGET_COLUMN}' "
            "is not present."
        )

        print(
            "\nThe current historical file contains GTFS "
            "schedule features, but it does not contain "
            "observed historical delay values."
        )

        print(
            "\nThis is expected and is NOT a model failure."
        )

        print(
            "\nWe must obtain real historical delay observations "
            "before training a supervised delay prediction model."
        )

        print(
            "\nIMPORTANT:"
            "\nDo NOT use scheduled travel time as delay."
            "\nDo NOT create artificial delay labels."
        )

        print("\nCurrent dataset:")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
        print(f"  Target: {TARGET_COLUMN} -> NOT FOUND")

        print("\nNext stage:")
        print(
            "  1. Build the historical delay target dataset"
            "\n  2. Validate delay_seconds"
            "\n  3. Train the baseline ML model"
            "\n  4. Evaluate the model"
            "\n  5. Save the trained model"
        )

        sys.exit(0)

    # --------------------------------------------------------
    # Target validation
    # --------------------------------------------------------

    target = pd.to_numeric(
        df[TARGET_COLUMN],
        errors="coerce"
    )

    valid_target = target.notna().sum()

    print(f"\nValid delay observations: {valid_target}")

    if valid_target == 0:

        print(
            "\nERROR: delay_seconds exists, "
            "but contains no valid numeric values."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Basic target statistics
    # --------------------------------------------------------

    print("\nDelay target statistics:")

    print(f"Minimum delay: {target.min():.2f} seconds")
    print(f"Maximum delay: {target.max():.2f} seconds")
    print(f"Average delay: {target.mean():.2f} seconds")
    print(f"Median delay: {target.median():.2f} seconds")

    # --------------------------------------------------------
    # Prepare output directory
    # --------------------------------------------------------

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --------------------------------------------------------
    # Save validated training dataset
    # --------------------------------------------------------

    training_df = df.copy()
    training_df[TARGET_COLUMN] = target

    output_file = os.path.join(
        OUTPUT_DIR,
        "delay_training_dataset.csv"
    )

    training_df.to_csv(
        output_file,
        index=False
    )

    print("\nSaved validated training dataset to:")
    print(output_file)

    print("\nDelay model training preparation completed successfully!")


if __name__ == "__main__":
    main()