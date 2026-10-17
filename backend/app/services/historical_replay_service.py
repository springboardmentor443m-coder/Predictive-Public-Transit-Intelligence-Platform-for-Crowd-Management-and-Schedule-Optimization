
import time
from bisect import bisect_right
from datetime import datetime, timedelta
from threading import Lock

import pandas as pd

from app.services.monitoring_service import (
    _load_flow_data,
    get_network_monitoring,
)

_replay_lock = Lock()
_replay_started_at = None
_replay_timestamps = None
_cached_observation_key = None
_cached_observation_result = None

# Visible replay begins after the warm-up day.
# Historical records from 11 August remain available
# to calculate prediction features.
REPLAY_START = datetime(2025, 8, 12, 0, 0, 0)
REPLAY_END = datetime(2025, 10, 1, 0, 0, 0)

# One replay-clock second per real second.
REPLAY_TOTAL_SECONDS = int(
    (REPLAY_END - REPLAY_START).total_seconds()
)


def _get_replay_timestamps():
    """Load actual timestamps available in the source dataset."""
    global _replay_timestamps

    if _replay_timestamps is not None:
        return _replay_timestamps

    df = _load_flow_data()

    if df.empty:
        raise ValueError("The historical BMRCL dataset is empty.")

    if "Timestamp" not in df.columns:
        raise ValueError(
            "The historical dataset does not contain a Timestamp column."
        )

    parsed = pd.to_datetime(df["Timestamp"], errors="coerce")
    actual_timestamps = set()

    for value in parsed.dropna():
        timestamp = pd.Timestamp(value).to_pydatetime()

        if REPLAY_START <= timestamp < REPLAY_END:
            actual_timestamps.add(timestamp)

    if not actual_timestamps:
        raise ValueError(
            "No historical observations were found between "
            "2025-08-12 and 2025-09-30."
        )

    _replay_timestamps = sorted(actual_timestamps)
    return _replay_timestamps


def get_next_historical_replay():
    """
    Advance the historical replay clock at 1x speed.

    Source observations are historical records. The replay clock
    advances continuously, but the selected observation changes
    only when the next source timestamp becomes available.
    """
    global _replay_started_at
    global _cached_observation_key
    global _cached_observation_result

    with _replay_lock:
        timestamps = _get_replay_timestamps()

        if not timestamps:
            raise ValueError(
                "No historical observations are available for replay."
            )

        if _replay_started_at is None:
            _replay_started_at = time.monotonic()

        elapsed_seconds = int(
            time.monotonic() - _replay_started_at
        )

        replay_elapsed_seconds = (
            elapsed_seconds % REPLAY_TOTAL_SECONDS
        )

        replay_clock = REPLAY_START + timedelta(
            seconds=replay_elapsed_seconds
        )

        # Select the latest actual observation at or before
        # the replay clock. Do not invent intermediate observations.
        timestamp_index = bisect_right(
            timestamps, replay_clock
        ) - 1

        if timestamp_index < 0:
            timestamp_index = 0

        observation_timestamp = timestamps[timestamp_index]

        observation_key = (
            observation_timestamp.date(),
            observation_timestamp.hour,
        )

        # Cache the result for the current source date and hour.
        if (
            observation_key != _cached_observation_key
            or _cached_observation_result is None
        ):
            result = get_network_monitoring(
                selected_date=observation_timestamp.date(),
                selected_hour=observation_timestamp.hour,
            )

            result["station_snapshots"] = [
                dict(snapshot)
                for snapshot in result.get("station_snapshots", [])
            ]

            for snapshot in result["station_snapshots"]:
                snapshot["observed_entries"] = (
                    snapshot.get("current_ridership")
                )
                snapshot["observed_exits"] = (
                    snapshot.get("current_exit")
                )
                snapshot["predicted_demand"] = (
                    snapshot.get("predicted_next_hour_ridership")
                )

            _cached_observation_result = result
            _cached_observation_key = observation_key

        # Copy the cached response before adding replay metadata.
        response = dict(_cached_observation_result)

        response["replay"] = True
        response["simulation"] = True
        response["is_live_feed"] = False
        response["data_source"] = "historical_csv_replay"

        response["replay_timestamp"] = replay_clock.isoformat()
        response["observation_timestamp"] = (
            observation_timestamp.isoformat()
        )

        response["replay_elapsed_seconds"] = replay_elapsed_seconds
        response["replay_total_seconds"] = REPLAY_TOTAL_SECONDS
        response["replay_progress_percent"] = round(
            replay_elapsed_seconds / REPLAY_TOTAL_SECONDS * 100,
            4,
        )

        response["replay_step"] = replay_elapsed_seconds + 1
        response["replay_total_steps"] = REPLAY_TOTAL_SECONDS

        response["assessment_type"] = "real-time-historical-replay"
        response["observation_note"] = (
            "Historical BMRCL observations are replayed at 1x clock "
            "speed: one replay-clock second per real second. The replay "
            "clock advances continuously, while the selected source "
            "observation changes only when a recorded timestamp is "
            "reached. No missing observations are fabricated. ML "
            "predictions depend on the available model features. "
            "This is not a genuine live BMRCL feed."
        )

        return response
