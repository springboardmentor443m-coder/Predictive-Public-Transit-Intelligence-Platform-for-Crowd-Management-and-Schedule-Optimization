import os
import joblib
import pandas as pd


MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "../ml/demand_model.joblib"
)


_model_data = None


def load_model():
    global _model_data

    if _model_data is None:
        _model_data = joblib.load(MODEL_PATH)

    return _model_data


def predict_demand(
    hour,
    day_of_week,
    day_of_year,
    month,
    lag_1,
    lag_24,
    lag_168
):
    data = load_model()

    model = data["model"]
    features = data["features"]

    input_data = pd.DataFrame([{
        "hour": hour,
        "day_of_week": day_of_week,
        "day_of_year": day_of_year,
        "month": month,
        "lag_1": lag_1,
        "lag_24": lag_24,
        "lag_168": lag_168
    }])

    prediction = model.predict(input_data[features])[0]

    return {
        "predicted_ridership": round(float(prediction), 2)
    }
