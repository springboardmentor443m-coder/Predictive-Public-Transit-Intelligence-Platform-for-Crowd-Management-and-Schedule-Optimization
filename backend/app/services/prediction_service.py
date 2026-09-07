from typing import List
from app.ml.inference import ml_inference
from app.services.crowd_service import live_station_state
from app.schemas.prediction_schema import StationForecastResponse, CongestionAnomalyAlert


class PredictionService:
    @staticmethod
    async def get_station_forecast(station_id: int, horizon_minutes: int = 30) -> StationForecastResponse:
        st_data = live_station_state.get(station_id)
        if not st_data:
            # Fallback for station 1
            st_data = list(live_station_state.values())[0]

        inflow = st_data["inflow_rate_ppm"]
        outflow = st_data["outflow_rate_ppm"]
        density = st_data["density_percentage"]

        forecast_data = ml_inference.forecast_station_demand(
            station_id=st_data["station_id"],
            current_inflow=inflow,
            current_outflow=outflow,
            current_density=density,
            horizon_minutes=horizon_minutes
        )
        return StationForecastResponse(**forecast_data)

    @staticmethod
    async def get_all_station_forecasts(horizon_minutes: int = 30) -> List[StationForecastResponse]:
        forecasts = []
        for st_id in live_station_state.keys():
            fc = await PredictionService.get_station_forecast(st_id, horizon_minutes)
            forecasts.append(fc)
        return forecasts

    @staticmethod
    async def get_congestion_anomalies() -> List[CongestionAnomalyAlert]:
        anomalies = []
        for st_data in live_station_state.values():
            if st_data["density_percentage"] >= 78.0:
                anomalies.append(CongestionAnomalyAlert(
                    station_id=st_data["station_id"],
                    station_name=st_data["station_name"],
                    line_name=st_data["line_name"],
                    timestamp=st_data["last_updated"].strftime("%H:%M:%S"),
                    anomaly_score=round(st_data["density_percentage"] / 100.0, 2),
                    predicted_bottleneck_time="In 15 minutes",
                    suggested_action=f"Increase train frequency on {st_data['line_name']} by +2 trains/hr or open secondary bypass exit gates."
                ))
        return anomalies


prediction_service = PredictionService()
