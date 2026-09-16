from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.schemas.prediction import DelayPredictResponse, DelayRequest
from app.services.prediction_service import (
    forecast_demand,
    predict_crowd,
    predict_delay,
    smart_recommendations,
    traffic_patterns,
)

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/crowd", response_model=list[dict])
async def crowd_prediction(station_id: str = Query(None), hours: int = Query(12, ge=1, le=48), db: Session = Depends(get_db), _=Depends(require_roles())):
    return predict_crowd(station_id, hours, db=db)


@router.get("/demand", response_model=list[dict])
async def demand_forecast(station_id: str = Query(None), hours: int = Query(12, ge=1, le=48), db: Session = Depends(get_db), _=Depends(require_roles())):
    return forecast_demand(station_id, hours, db=db)


@router.post("/delay", response_model=DelayPredictResponse)
async def delay_prediction(req: DelayRequest, _=Depends(require_roles())):
    from fastapi import HTTPException

    try:
        return predict_delay(req)
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail="Delay prediction model is temporarily unavailable. Please retry after training.",
        ) from e


@router.get("/recommendations", response_model=list[dict])
async def recommendations(db: Session = Depends(get_db), _=Depends(require_roles())):
    return smart_recommendations(db)


@router.get("/patterns", response_model=list[dict])
async def patterns(db: Session = Depends(get_db), _=Depends(require_roles())):
    return traffic_patterns(db)


@router.get("/model-info", response_model=dict)
async def model_info(db: Session = Depends(get_db), _=Depends(require_roles())):
    """Expose loaded model metadata so dashboards can show real model
    provenance (city, algorithm, metrics, dataset source)."""
    import os

    from app.ml import registry
    from app.ml.model_wrappers import get_crowd_model, get_demand_model, get_delay_model

    crowd = get_crowd_model()
    demand = get_demand_model()
    delay = get_delay_model()
    city = registry.model_city()

    def _metrics(kind: str, c: str):
        import json

        # Metrics live at repo-root kaggle/{city}_model_outputs/metrics.json with
        # top-level "crowd"/"demand" keys (e.g. kaggle/hangzhou_model_outputs/metrics.json).
        # predictions.py is backend/app/api/v1/... -> 5 dirnames reaches repo root.
        repo = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))))
        )
        names = (f"{c}_model_outputs/metrics.json", f"{c}_{kind}_model_outputs/metrics.json", f"{kind}_model_outputs/metrics.json")
        for name in names:
            for base in (os.path.join(repo, "kaggle", name), os.path.join(os.getcwd(), "kaggle", name)):
                if os.path.exists(base):
                    try:
                        with open(base) as f:
                            data = json.load(f)
                        # metrics.json nests under "crowd"/"demand" key
                        if isinstance(data, dict) and kind in data and isinstance(data[kind], dict):
                            return data[kind]
                        return data
                    except Exception:
                        continue
        return {}

    crowd_m = _metrics("crowd", city)
    demand_m = _metrics("demand", city)
    delay_m = _metrics("delay", "nj_transit")
    delay_metrics = {
        "auc": (delay_m.get("delay_classifier", {}).get("roc_auc") or delay_m.get("roc_auc")),
        "mae": (delay_m.get("delay_regressor", {}).get("mae") or delay_m.get("mae")),
        "accuracy": (delay_m.get("delay_classifier", {}).get("accuracy") or delay_m.get("accuracy")),
    }
    return {
        "city": city,
        "supported_cities": list(registry.SUPPORTED_CITIES),
        "station_map": registry.CITY_STATION_MAP.get(city, {}),
        "crowd": {
            "loaded": crowd.is_loaded,
            "is_kaggle": crowd.is_kaggle,
            "trained_on": crowd.trained_on,
            "algorithm": "XGBoost" if crowd.is_kaggle else "GradientBoostingRegressor",
            "metrics": {k: crowd_m.get(k) for k in ("r2", "mae", "rmse", "peak_hour_mae") if k in crowd_m},
        },
        "demand": {
            "loaded": demand.is_loaded,
            "is_kaggle": demand.is_kaggle,
            "trained_on": demand.trained_on,
            "algorithm": "XGBoost" if demand.is_kaggle else "GradientBoostingRegressor",
            "metrics": {k: demand_m.get(k) for k in ("r2", "mae", "rmse") if k in demand_m},
        },
        "delay": {
            "loaded": delay.is_loaded,
            "trained_on": delay.trained_on,
            "algorithm": "XGBoost classifier + regressor",
            "classes": delay.classes,
            "metrics": {k: v for k, v in delay_metrics.items() if v is not None},
        },
        "datasets": {
            "seoul": "kimjmin/seoul-metro-usage (2015-2021 entry/exit)",
            "hangzhou": "zjplab/hangzhou-metro-traffic-prediction (Jan 2019, 81 stations)",
            "nj_transit": "pranavbadami/nj-transit-amtrak-nec-performance (2018-2019 delays)",
            "nyc": "eddeng/nyc-subway-traffic-data-20172021 (469 stations)",
            "tfl": "olisao/transport-for-london-tfl-entry-and-exit-dataset (435 stations)",
            "beijing": "itsncut/data-of-metro-passengers-in-beijing (Jan 2019 O-D)",
            "railway2015": "anuragraturi/railway-delay-dataset (312k journeys, 2015)",
        },
    }
