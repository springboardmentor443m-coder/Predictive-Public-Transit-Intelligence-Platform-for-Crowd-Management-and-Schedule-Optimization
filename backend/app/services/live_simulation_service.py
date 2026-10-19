
from copy import deepcopy
from datetime import datetime
from threading import Lock
import random

from app.services.monitoring_service import (
    get_network_monitoring,
    _pressure_level,
)

_lock = Lock()
_rng = random.Random()
_live_state = None


def _initialize_simulation():
    """Initialize simulated activity from historical monitoring and ML results."""
    global _live_state

    baseline = get_network_monitoring()
    stations = {}

    for original in baseline.get("station_snapshots", []):
        snapshot = deepcopy(original)
        station = snapshot["station"]

        baseline_ridership = max(
            0, int(snapshot.get("current_ridership") or 0)
        )
        baseline_exit = max(
            0, int(snapshot.get("current_exit") or 0)
        )

        raw_prediction = snapshot.get(
            "ml_predicted_next_hour_ridership"
        )
        if raw_prediction is None:
            raw_prediction = snapshot.get(
                "predicted_next_hour_ridership"
            )

        baseline_prediction = max(
            0.0, float(raw_prediction or 0)
        )

        stations[station] = {
            "data": snapshot,
            "baseline_ridership": baseline_ridership,
            "baseline_exit": baseline_exit,
            "baseline_prediction": baseline_prediction,
        }

    _live_state = {
        "stations": stations,
        "baseline_observation_date": baseline.get("monitoring_date"),
        "baseline_observation_hour": baseline.get("monitoring_hour"),
    }


def _simulate_count(previous, percentage):
    """Apply a small, bounded simulated change to a passenger count."""
    previous = max(0, int(previous or 0))

    if previous == 0:
        return _rng.choice([0, 0, 0, 1])

    change = _rng.uniform(-percentage, percentage)
    updated = max(0, int(round(previous * (1 + change))))

    if updated == previous:
        updated = max(
            0, previous + _rng.choice([-1, 1])
        )

    return updated



def _relative_pressure(current, predicted, max_current, max_predicted):
    """
    Calculate a stable, historical-range-based demand pressure score.

    The score uses the network-relative current and predicted demand.
    It is an analytical indicator, not measured occupancy or confirmed
    physical congestion.
    """
    current_component = (
        (current / max_current) * 100
        if max_current > 0
        else 0.0
    )

    predicted_component = (
        (predicted / max_predicted) * 100
        if max_predicted > 0
        else 0.0
    )

    score = (
        0.65 * current_component
        + 0.35 * predicted_component
    )

    return round(max(0.0, min(score, 100.0)), 2)



def get_live_network_monitoring():
    """Return evolving simulated station activity based on historical data."""
    global _live_state

    with _lock:
        if _live_state is None:
            _initialize_simulation()

        snapshots = []

        for station, station_state in _live_state["stations"].items():
            snapshot = station_state["data"]

            previous_entries = snapshot.get("current_ridership") or 0
            previous_exits = snapshot.get("current_exit") or 0

            current_entries = _simulate_count(previous_entries, 0.015)
            current_exits = _simulate_count(previous_exits, 0.02)

            snapshot["current_entries"] = current_entries
            snapshot["current_ridership"] = current_entries
            snapshot["current_exit"] = current_exits
            snapshot["net_flow"] = current_entries - current_exits

            baseline_entries = station_state["baseline_ridership"]
            baseline_prediction = station_state["baseline_prediction"]

            if baseline_entries > 0:
                demand_ratio = current_entries / baseline_entries
            elif current_entries > 0:
                # No usable baseline: avoid forcing the prediction to zero.
                # Use the simulated entry count as a conservative fallback.
                demand_ratio = 1.0
                baseline_prediction = float(current_entries)
            else:
                demand_ratio = 1.0

            predicted = round(
                max(0.0, baseline_prediction * demand_ratio), 2
            )

            snapshot["predicted_next_hour_ridership"] = predicted
            snapshot["ml_predicted_next_hour_ridership"] = predicted

            # No actual next-hour observation is available in this demo.
            snapshot["observed_next_hour_ridership"] = None
            snapshot["prediction_error"] = None
            snapshot["prediction_error_percentage"] = None

            snapshot["assessment_type"] = "simulated-live-demand"
            snapshot["simulation"] = True
            snapshot["data_available"] = True
            snapshot["prediction_available"] = True

            snapshots.append(deepcopy(snapshot))

        max_current = max(
            (row["current_ridership"] for row in snapshots),
            default=0,
        )
        max_predicted = max(
            (
                row["predicted_next_hour_ridership"]
                for row in snapshots
            ),
            default=0.0,
        )

        pressure_levels = {
            "LOW": 0,
            "MODERATE": 0,
            "HIGH": 0,
            "CRITICAL": 0,
        }

        for snapshot in snapshots:
            pressure = _relative_pressure(
                current=snapshot["current_ridership"],
                predicted=snapshot["predicted_next_hour_ridership"],
                max_current=max_current,
                max_predicted=max_predicted,
            )

            level = _pressure_level(pressure)

            snapshot["pressure_score"] = pressure
            snapshot["congestion_level"] = level
            snapshot["pressure_basis"] = (
                "network_relative_simulated_demand"
            )

            station = snapshot["station"]
            _live_state["stations"][station]["data"] = deepcopy(snapshot)

            pressure_levels[level] += 1

        highest_current = (
            max(
                snapshots,
                key=lambda row: row["current_ridership"],
            )
            if snapshots
            else None
        )

        highest_predicted = (
            max(
                snapshots,
                key=lambda row: row["predicted_next_hour_ridership"],
            )
            if snapshots
            else None
        )

        simulation_time = datetime.now().astimezone()

        return {
            "stations_monitored": len(snapshots),
            "monitoring_date": simulation_time.strftime("%Y-%m-%d"),
            "monitoring_hour": simulation_time.hour,
            "simulation_timestamp": simulation_time.isoformat(),
            "baseline_observation_date": (
                _live_state["baseline_observation_date"]
            ),
            "baseline_observation_hour": (
                _live_state["baseline_observation_hour"]
            ),
            "pressure_levels": pressure_levels,
            "high_pressure_stations": (
                pressure_levels["HIGH"] + pressure_levels["CRITICAL"]
            ),
            "highest_current_ridership": highest_current,
            "highest_predicted_ridership": highest_predicted,
            "station_snapshots": snapshots,
            "assessment_type": "simulated-live-demand",
            "data_source": "historical_baseline_with_simulation",
            "is_live_feed": False,
            "simulation": True,
            "pressure_basis": "network_relative_simulated_demand",
            "observation_note": (
                "Demonstration only. Passenger activity is simulated "
                "from historical monitoring results and is not actual "
                "current BMRCL passenger data. Predictions are historical "
                "ML estimates adjusted for simulated demand. Pressure "
                "scores are relative network indicators, not measured "
                "occupancy or confirmed physical congestion."
            ),
            "updated_at": simulation_time.isoformat(),
        }
