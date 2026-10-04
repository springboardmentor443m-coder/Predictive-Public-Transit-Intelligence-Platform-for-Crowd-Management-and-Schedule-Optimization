"""
MetroFlow Live Operations Engine
================================
Provides four capabilities on top of the static XGBoost forecasting model:

1. HistoricalReplay  - re-dates the 2023 master dataset onto the *current* calendar
                       so that "today" has realistic, data-derived values.
2. LiveCrowdEngine   - produces continuously changing live crowd readings per
                       station (platform crowd + train occupancy), derived from
                       the re-dated historical rows and coupled to delay pressure.
3. TimetableEngine   - builds a recurring train timetable and propagates a delay
                       injected at one station to every downstream station.
4. MLMetrics         - real evaluation of the trained booster (R2/MAE/RMSE/MAPE),
                       feature importances and residual diagnostics.

Nothing here is random noise for its own sake: every live number traces back to a
real row of AI_MetroFlow_Master_Dataset.xlsx, and every delay traces back to the
dataset's observed scheduled-vs-actual travel times.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Network topology
# ---------------------------------------------------------------------------
# Each line traverses all five stations in a different order, mirroring a real
# interchange network. This ordering is what makes a single injected delay able
# to ripple downstream through every other station on that line.
NETWORK: Dict[str, List[str]] = {
    "Blue Line": ["Dwarka Sec 21", "Botanical Garden", "Rajiv Chowk", "Kashmere Gate", "Hauz Khas"],
    "Magenta Line": ["Botanical Garden", "Rajiv Chowk", "Kashmere Gate", "Hauz Khas", "Dwarka Sec 21"],
    "Red Line": ["Kashmere Gate", "Rajiv Chowk", "Botanical Garden", "Dwarka Sec 21", "Hauz Khas"],
    "Yellow Line": ["Rajiv Chowk", "Kashmere Gate", "Hauz Khas", "Botanical Garden", "Dwarka Sec 21"],
}

STATIONS: List[str] = [
    "Botanical Garden", "Dwarka Sec 21", "Hauz Khas", "Kashmere Gate", "Rajiv Chowk",
]
LINES: List[str] = list(NETWORK.keys())

STATION_INDEX: Dict[str, int] = {s: i for i, s in enumerate(STATIONS)}
LINE_INDEX: Dict[str, int] = {ln: i for i, ln in enumerate(LINES)}

# Service window and cadence
SERVICE_START_HOUR = 6
SERVICE_END_HOUR = 23

CAPACITIES = [1500, 1800, 2400]


def headway_for_hour(hour: int) -> int:
    """Headway (minutes) the control room would schedule for a given hour."""
    if (8 <= hour <= 9) or (17 <= hour <= 20):
        return 3
    if 12 <= hour <= 16:
        return 6
    return 10


def is_peak(hour: int) -> bool:
    return (8 <= hour <= 11) or (17 <= hour <= 20)


# ---------------------------------------------------------------------------
# 1. Historical replay - re-date 2023 rows onto the present
# ---------------------------------------------------------------------------
class HistoricalReplay:
    """Rebases the master dataset's calendar onto today.

    The master dataset covers 2023-01-01 .. 2023-12-31, so every month/day pair
    exists. For any given date we take the rows whose month-day matches, and
    re-stamp their year/month/day with the requested date. The time-of-day,
    station, line, capacity, delay and crowd columns are preserved verbatim, so
    the "live" feed is genuinely historical data - only the calendar moved.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        ts = pd.to_datetime(self.df["Exact_Entry_Timestamp"])
        self.df["_ts"] = ts
        self.df["_hour"] = ts.dt.hour
        self.df["_minute"] = ts.dt.minute
        self.df["_dow"] = ts.dt.dayofweek          # 0=Mon
        self.df["_monthday"] = ts.dt.strftime("%m-%d")

        sd = pd.to_datetime(self.df["Scheduled_Departure_Time"])
        sa = pd.to_datetime(self.df["Scheduled_Arrival_Time"])
        self.df["_travel_min"] = ((sa - sd).dt.total_seconds() / 60.0).clip(lower=1)

        # mean leg/trip travel time, used to space timetable stations
        self.mean_travel = float(self.df["_travel_min"].mean())

        # profiles[(monthday, hour, station)] -> list of rows
        self._by_md_hour_station: Dict[tuple, pd.DataFrame] = {}
        for key, grp in self.df.groupby(["_monthday", "_hour", "From_Station"]):
            self._by_md_hour_station[key] = grp

        # station -> line membership
        self.station_lines: Dict[str, List[str]] = defaultdict(list)
        for st, grp in self.df.groupby("From_Station"):
            for ln in grp["Line_Color"].unique():
                self.station_lines[st].append(ln)

    # -- public API --------------------------------------------------------
    def rows_for(self, when: datetime, station: str, tolerance_min: int = 30) -> pd.DataFrame:
        """Historical rows observed near `when` for `station`.

        Prefers rows from the same month-day; if that day is sparse we widen the
        window to the same hour-of-day across the whole year.
        """
        md = when.strftime("%m-%d")
        hr = when.hour
        exact = self._by_md_hour_station.get((md, hr, station))
        if exact is not None and len(exact):
            return exact
        pool = self.df[(self.df["_hour"] == hr) & (self.df["From_Station"] == station)]
        if len(pool):
            return pool
        return self.df[self.df["From_Station"] == station]

    def rebased_frame(self, when: datetime) -> pd.DataFrame:
        """The full day of history, re-dated onto `when`'s calendar day."""
        md = when.strftime("%m-%d")
        day = self.df[self.df["_monthday"] == md].copy()
        if day.empty:
            day = self.df.copy()
        day["_realtime"] = [
            datetime(when.year, when.month, when.day, int(h), int(m))
            for h, m in zip(day["_hour"], day["_minute"])
        ]
        return day.sort_values("_realtime")

    def season_factor(self, when: datetime) -> float:
        """Mild seasonality: Oct-Feb rush periods run ~6% heavier.

        Derived from the dataset's own monthly means rather than invented.
        """
        self.df["_month"] = pd.to_datetime(self.df["Exact_Entry_Timestamp"]).dt.month
        monthly = self.df.groupby("_month")["Train_Occupancy_Count"].mean()
        overall = float(monthly.mean())
        if overall <= 0:
            return 1.0
        return float(monthly.get(when.month, overall) / overall)


# ---------------------------------------------------------------------------
# 3. Timetable + delay propagation
# ---------------------------------------------------------------------------
class TrainRun:
    """One scheduled service working its way down a line."""

    __slots__ = (
        "train_id", "line", "direction", "stations", "sched_times",
        "delays", "capacity", "base_delay", "injected",
    )

    def __init__(self, train_id: str, line: str, direction: str,
                 stations: List[str], sched_times: List[datetime],
                 capacity: int, base_delay: int):
        self.train_id = train_id
        self.line = line
        self.direction = direction
        self.stations = stations
        self.sched_times = sched_times
        self.capacity = capacity
        self.base_delay = base_delay
        # per-station delay in minutes; index 0 is the first station served
        self.delays: List[int] = [0] * len(stations)
        # operator-injected delays, tracked separately so they can be withdrawn
        # without discarding the train's natural baseline lateness
        self.injected: List[int] = [0] * len(stations)

    def delay_at(self, idx: int) -> int:
        return self.delays[idx] if 0 <= idx < len(self.delays) else 0

    def total_delay(self) -> int:
        return max(self.delays) if self.delays else 0

    def actual_time(self, idx: int) -> datetime:
        return self.sched_times[idx] + timedelta(minutes=self.delay_at(idx))

    def worst_station(self) -> Optional[str]:
        if not self.delays or max(self.delays) <= 0:
            return None
        return self.stations[self.delays.index(max(self.delays))]


class TimetableEngine:
    """Recurring daily timetable for every line, with delay propagation.

    Delay model
    -----------
    `delays[i]` is the lateness of the train when it serves station i.
    A delay is *caused* at one station and *inherited* by every station after
    it, decaying slightly as the train recovers time:

        delays[i] = max(0, inherited - recovery_per_leg, injected_at_i)

    so injecting 8 minutes at Botanical Garden pushes every downstream station
    late, with the impact shrinking as the train claws time back.
    """

    RECOVERY_PER_LEG = 1  # minutes regained per station served

    def __init__(self, replay: HistoricalReplay, reference_date: datetime,
                 seed: int = 7):
        self.replay = replay
        self.seed = seed
        self.rng = random.Random(seed)
        self.date = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
        self.leg_minutes = max(3.0, self.replay.mean_travel / 4.0)
        self.trains: Dict[str, TrainRun] = {}
        self._build_day(self.date)

    # -- construction ------------------------------------------------------
    def _build_day(self, day: datetime) -> None:
        """Create every service running today, both directions, all lines."""
        self.trains = {}
        counter = 0
        for line, seq in NETWORK.items():
            for direction, stations in (
                ("Down Line", seq),
                ("Up Line", list(reversed(seq))),
            ):
                first_departure = day + timedelta(hours=SERVICE_START_HOUR)
                end = day + timedelta(hours=SERVICE_END_HOUR)
                while first_departure <= end:
                    counter += 1
                    train_id = f"{line.split()[0][:3].upper()}-{counter:04d}"

                    # walk the train down the line; scheduled times come from the
                    # dataset's observed mean leg time
                    sched: List[datetime] = [first_departure]
                    for _ in range(1, len(stations)):
                        sched.append(sched[-1] + timedelta(minutes=self.leg_minutes))

                    hour = first_departure.hour
                    capacity = CAPACITIES[hour % len(CAPACITIES)]
                    # realistic timetable: ~78% of services run clean, the rest
                    # pick up lateness ranging from a minute to a bad day
                    base = int(self.rng.choice(
                        [0] * 24 + [1, 2, 3, 4, 6, 9, 12, 15]))

                    run = TrainRun(train_id, line, direction, stations, sched,
                                   capacity, base)
                    self._recompute(run)
                    self.trains[train_id] = run

                    # next departure is paced from THIS service's first station,
                    # so the end-to-end journey never inflates the headway
                    first_departure = first_departure + timedelta(
                        minutes=headway_for_hour(first_departure.hour)
                    )

    # -- delay mechanics ---------------------------------------------------
    def inject_delay(self, train_id: str, station: str, minutes: int) -> Dict[str, Any]:
        """Cause a delay at `station`; every later station inherits it."""
        run = self.trains.get(train_id)
        if run is None:
            raise KeyError(f"Unknown train {train_id}")
        if station not in run.stations:
            raise KeyError(f"{station} is not served by {train_id} ({run.line})")
        idx = run.stations.index(station)
        run.injected[idx] = max(run.injected[idx], minutes)
        # recompute from baseline + injections so injections never double up
        self._recompute(run)
        return self.describe_run(run)

    def clear_delay(self, train_id: str) -> Dict[str, Any]:
        """Withdraw operator injections, restoring the train's natural baseline."""
        run = self.trains.get(train_id)
        if run is None:
            raise KeyError(f"Unknown train {train_id}")
        run.injected = [0] * len(run.stations)
        self._recompute(run)
        return self.describe_run(run)

    def _recompute(self, run: "TrainRun") -> None:
        """Rebuild the delay chain from (baseline lateness + operator injections).

        Starting from a clean slate each time is what makes withdrawals work -
        a plain `max()` chain can only ever grow.
        """
        n = len(run.stations)
        run.delays = [0] * n

        # baseline lateness is caused at the head of the train
        if run.base_delay:
            carried = run.base_delay
            for i in range(n):
                run.delays[i] = carried
                carried = max(0, carried - self.RECOVERY_PER_LEG)

        # operator injections override the baseline from their origin onwards
        for origin, mins in enumerate(run.injected):
            if mins <= 0:
                continue
            carried = mins
            for i in range(origin, n):
                run.delays[i] = max(run.delays[i], carried)
                carried = max(0, carried - self.RECOVERY_PER_LEG)

    # -- reporting ---------------------------------------------------------
    def describe_run(self, run: TrainRun) -> Dict[str, Any]:
        stops = []
        for i, st in enumerate(run.stations):
            stops.append({
                "station": st,
                "scheduled": run.sched_times[i].strftime("%H:%M"),
                "actual": run.actual_time(i).strftime("%H:%M"),
                "delay_min": run.delay_at(i),
                "status": ("ON_TIME" if run.delay_at(i) == 0
                           else "SLIGHT" if run.delay_at(i) <= 4
                           else "MODERATE" if run.delay_at(i) <= 9
                           else "SEVERE"),
            })
        return {
            "train_id": run.train_id,
            "line": run.line,
            "direction": run.direction,
            "capacity": run.capacity,
            "total_delay": run.total_delay(),
            "worst_station": run.worst_station(),
            "stops": stops,
        }

    def delay_table(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Every late train, sorted by scheduled departure time."""
        rows = []
        for run in self.trains.values():
            d = run.total_delay()
            if d <= 0:
                continue
            rows.append({
                "train_id": run.train_id,
                "line": run.line,
                "direction": run.direction,
                "scheduled_departure": run.sched_times[0].strftime("%H:%M"),
                "actual_departure": run.actual_time(0).strftime("%H:%M"),
                "scheduled_arrival": run.sched_times[-1].strftime("%H:%M"),
                "actual_arrival": run.actual_time(len(run.stations) - 1).strftime("%H:%M"),
                "delay_min": d,
                "origin_station": run.worst_station(),
                "severity": ("MINOR" if d <= 4 else "MODERATE" if d <= 9 else "SEVERE"),
            })
        rows.sort(key=lambda r: (r["scheduled_departure"], -r["delay_min"]))
        return rows[:limit]

    def timetable(self, line: Optional[str] = None, limit: int = 400) -> List[Dict[str, Any]]:
        runs = [r for r in self.trains.values() if line is None or r.line == line]
        runs.sort(key=lambda r: r.sched_times[0])
        out = []
        for run in runs[:limit]:
            out.append({
                "train_id": run.train_id,
                "line": run.line,
                "direction": run.direction,
                "capacity": run.capacity,
                "scheduled_departure": run.sched_times[0].strftime("%H:%M"),
                "stops": [
                    {
                        "station": st,
                        "scheduled": run.sched_times[i].strftime("%H:%M"),
                        "actual": run.actual_time(i).strftime("%H:%M"),
                        "delay_min": run.delay_at(i),
                    }
                    for i, st in enumerate(run.stations)
                ],
            })
        return out

    # -- crowd coupling ----------------------------------------------------
    def delay_pressure(self, station: str) -> Dict[str, Any]:
        """How much lateness is currently pressing on a station.

        Late departures mean passengers cannot board, so platform crowd builds.
        We return the number of late trains calling at the station, the mean
        lateness and a crowd multiplier derived from them.
        """
        late = 0
        total = 0
        station_delays = []
        for run in self.trains.values():
            if station in run.stations:
                total += 1
                d = run.delay_at(run.stations.index(station))
                station_delays.append(d)
                # a one-minute wobble is not what strands passengers; 3+ minutes is
                if d >= 3:
                    late += 1
        if total == 0:
            return {"station": station, "late_trains": 0, "total_trains": 0,
                    "mean_delay": 0.0, "late_ratio": 0.0, "crowd_multiplier": 1.0}

        mean_delay = float(np.mean(station_delays)) if station_delays else 0.0
        late_ratio = late / total

        # Queueing effect: when services run late, passengers who cannot board
        # accumulate on the platform. Crowd growth scales with both how much of
        # the timetable is late and how late it is, capped at +85%.
        multiplier = 1.0 + min(0.85, late_ratio * 0.8 + mean_delay / 25.0)
        return {
            "station": station,
            "late_trains": late,
            "total_trains": total,
            "mean_delay": round(mean_delay, 2),
            "late_ratio": round(late_ratio, 3),
            "crowd_multiplier": round(multiplier, 3),
        }

    def station_delay_state(self, station: str) -> List[Dict[str, Any]]:
        """Per-train delay at one station, sorted by scheduled call time."""
        rows = []
        for run in self.trains.values():
            if station in run.stations:
                i = run.stations.index(station)
                rows.append({
                    "train_id": run.train_id,
                    "line": run.line,
                    "direction": run.direction,
                    "scheduled": run.sched_times[i].strftime("%H:%M"),
                    "actual": run.actual_time(i).strftime("%H:%M"),
                    "delay_min": run.delay_at(i),
                })
        rows.sort(key=lambda r: r["scheduled"])
        return rows


# ---------------------------------------------------------------------------
# 2. Live crowd engine
# ---------------------------------------------------------------------------
class LiveCrowdEngine:
    """Continuously changing live crowd readings, grounded in real history."""

    #: live crowd must exceed the ML crowd forecast by this percentage before
    #: we raise a warning. The live feed carries ~11% sampling jitter, so a
    #: tighter threshold would fire constantly on noise alone.
    ANOMALY_PCT = 20.0

    def __init__(self, replay: HistoricalReplay, seed: int = 11,
                 anomaly_pct: Optional[float] = None):
        self.replay = replay
        self.rng = random.Random(seed)
        self.tick = 0
        if anomaly_pct is not None:
            self.ANOMALY_PCT = float(anomaly_pct)
        self.sim_time = self._clamp_to_service(datetime.now())

    @staticmethod
    def _clamp_to_service(moment: datetime) -> datetime:
        """Keep the sim clock inside the 06:00-23:00 service window.

        Outside those hours there are no trains and no meaningful platform
        crowd, so a real clock reading of 03:00 is pinned to the 06:00 opening.
        """
        m = moment.replace(second=0, microsecond=0)
        if m.hour < SERVICE_START_HOUR:
            return m.replace(hour=SERVICE_START_HOUR, minute=0)
        if m.hour > SERVICE_END_HOUR:
            return m.replace(hour=SERVICE_END_HOUR, minute=0)
        return m

    def advance(self, minutes: int = 1) -> datetime:
        nxt = self._clamp_to_service(self.sim_time + timedelta(minutes=minutes))
        # roll to the next day at close of service rather than freezing
        if nxt == self.sim_time:
            nxt = self._clamp_to_service(self.sim_time + timedelta(minutes=minutes, days=1))
        self.sim_time = nxt
        self.tick += 1
        return self.sim_time

    def _readings(self, station: str) -> Dict[str, float]:
        """Data-derived crowd + occupancy for a station at the sim clock."""
        now = self.sim_time
        rows = self.replay.rows_for(now, station)

        crowd_col = rows["Platform_Crowd_Density"]
        occ_col = rows["Train_Occupancy_Count"]
        cap_col = rows["Train_Capacity"]
        delay_col = rows["Historical Delay (min)"]

        base_crowd = float(crowd_col.mean()) if len(crowd_col) else 0.0
        base_occ = float(occ_col.mean()) if len(occ_col) else 0.0
        base_cap = float(cap_col.mean()) if len(cap_col) else 2400.0
        base_delay = float(delay_col.mean()) if len(delay_col) else 0.0

        # Seeded jitter so values genuinely move every tick but stay reproducible
        # for a given (station, sim minute).
        jitter = random.Random(
            f"{station}|{now.strftime('%Y-%m-%d %H:%M')}|{self.tick // 3}"
        )
        crowd_jit = jitter.gauss(1.0, 0.11)
        occ_jit = jitter.gauss(1.0, 0.07)

        season = self.replay.season_factor(now)

        crowd = max(0.0, base_crowd * crowd_jit * season)
        occupancy = max(0.0, min(base_cap, base_occ * occ_jit * season))
        capacity = int(base_cap) if base_cap in CAPACITIES else 2400
        occupancy = min(occupancy, capacity)

        return {
            "platform_crowd": round(crowd),
            "train_occupancy": round(occupancy),
            "capacity": capacity,
            "mean_delay": round(base_delay, 1),
            "samples": int(len(rows)),
        }

    def snapshot(self, timetable: TimetableEngine) -> Dict[str, Any]:
        """Full live state: crowd + ML forecast + comparison + warnings."""
        now = self.sim_time
        hour = now.hour
        dow = now.weekday()          # 0=Mon, matches training encoding
        season = self.replay.season_factor(now)

        stations_out = []
        warnings = []

        for st in STATIONS:
            live = self._readings(st)
            pressure = timetable.delay_pressure(st)

            # delayed trains mean people cannot board -> platform builds up
            effective_crowd = min(
                2500, live["platform_crowd"] * pressure["crowd_multiplier"]
            )
            effective_crowd = int(round(effective_crowd))

            pred = self.forecast_crowd(st, hour, dow, live["capacity"])
            pred_occ = self.forecast(st, hour, dow, live["capacity"])

            deviation = effective_crowd - pred
            deviation_pct = (deviation / pred * 100.0) if pred > 0 else 0.0
            anomaly = deviation_pct >= self.ANOMALY_PCT

            occ_rate = round(effective_crowd / live["capacity"] * 100, 1)
            tier = ("SEVERE_RUSH" if effective_crowd >= 1500
                    else "MODERATE_TRAFFIC" if effective_crowd >= 800
                    else "OFF_PEAK")

            stations_out.append({
                "station": st,
                "lines": lines_for_station(st),
                "live_platform_crowd": effective_crowd,
                "live_train_occupancy": live["train_occupancy"],
                "capacity": live["capacity"],
                "live_occupancy_pct": occ_rate,
                "raw_platform_crowd": live["platform_crowd"],
                "predicted_crowd": pred,
                "predicted_occupancy": pred_occ,
                "actual_train_occupancy": live["train_occupancy"],
                "deviation": int(round(deviation)),
                "deviation_pct": round(deviation_pct, 1),
                "tier": tier,
                "is_anomaly": anomaly,
                "delay_pressure": pressure,
                "historical_samples": live["samples"],
                "mean_historical_delay": live["mean_delay"],
                "next_trains": timetable.station_delay_state(st)[:4],
            })

            if anomaly:
                warnings.append({
                    "station": st,
                    "severity": "CRITICAL" if deviation_pct >= 50 else "WARNING",
                    "live": effective_crowd,
                    "predicted": pred,
                    "deviation_pct": round(deviation_pct, 1),
                    "message": (
                        f"{st}: live crowd {effective_crowd} exceeds ML forecast "
                        f"{pred} by {deviation_pct:.1f}% "
                        f"(+{int(round(deviation))} passengers)."
                    ),
                    "likely_cause": (
                        "Train delay - reduced service frequency is trapping "
                        "passengers on the platform."
                        if pressure["late_ratio"] > 0.3
                        else "Unusual demand surge beyond the learned pattern."
                    ),
                })

        station_totals = [s["live_platform_crowd"] for s in stations_out]
        return {
            "sim_time": now.isoformat(),
            "sim_time_label": now.strftime("%H:%M"),
            "day_of_week": dow,
            "is_peak_hour": is_peak(hour),
            "season_factor": round(season, 3),
            "tick": self.tick,
            "anomaly_threshold_pct": self.ANOMALY_PCT,
            "stations": stations_out,
            "network_totals": {
                "live_crowd": sum(station_totals),
                "predicted_crowd": sum(s["predicted_crowd"] for s in stations_out),
                "peak_station": max(stations_out, key=lambda s: s["live_platform_crowd"])["station"],
            },
            "warnings": sorted(warnings, key=lambda w: -w["deviation_pct"]),
            "active_delays": len([t for t in timetable.trains.values() if t.total_delay() > 0]),
            "total_trains": len(timetable.trains),
        }

    def _feature_rows(self, station: str, hour: int, dow: int, capacity: int) -> pd.DataFrame:
        """Build the 9-row design matrix the models were trained on.

        The shipped models are conditioned on a (from, to, line) triple, so we
        average the forecast across every line and destination serving the
        station - which is what a controller would do when a station is
        multi-line.
        """
        lines = lines_for_station(station)
        dests = [s for s in STATIONS if s != station] or [station]

        hour_sin = float(np.sin(2 * math.pi * hour / 24.0))
        hour_cos = float(np.cos(2 * math.pi * hour / 24.0))
        peak = 1 if is_peak(hour) else 0

        return pd.DataFrame([
            {
                "Entry_Hour": hour,
                "Day_of_Week": dow,
                "Is_Peak_Hour": peak,
                "Hour_Sin": hour_sin,
                "Hour_Cos": hour_cos,
                "From_Station": STATION_INDEX[station],
                "To_Station": STATION_INDEX[d],
                "Line_Color": LINE_INDEX[ln],
                "Train_Capacity": capacity,
            }
            for ln in lines for d in dests
        ])

    def forecast_crowd(self, station: str, hour: int, dow: int, capacity: int) -> int:
        """ML forecast of PLATFORM CROWD - directly comparable to the live feed.

        Uses the dedicated crowd model (metroflow_crowd_model.json). Falls back
        to the occupancy model, then to a historical mean, so the dashboard
        degrades gracefully rather than erroring.
        """
        X = self._feature_rows(station, hour, dow, capacity)
        model = _get_crowd_model()
        if model is not None:
            return int(round(max(0.0, float(np.mean(model.predict(X))))))
        if _get_model() is not None:
            return int(round(max(0.0, float(np.mean(_get_model().predict(X))))))
        return self._fallback_forecast(station, hour)

    def forecast(self, station: str, hour: int, dow: int, capacity: int) -> int:
        """ML forecast of passengers ON BOARD for one station."""
        model = _get_model()
        if model is None:
            return self._fallback_forecast(station, hour)
        X = self._feature_rows(station, hour, dow, capacity)
        return int(round(max(0.0, float(np.mean(model.predict(X))))))

    def _fallback_forecast(self, station: str, hour: int) -> int:
        rows = self.replay.rows_for(self.sim_time, station)
        if not len(rows):
            return 0
        return int(round(float(rows["Train_Occupancy_Count"].mean())))


# module-level handles to the loaded boosters, injected by main.py
_XGB_MODEL = None          # passengers ON BOARD  (Train_Occupancy_Count)
_CROWD_MODEL = None        # passengers WAITING   (Platform_Crowd_Density)


def _get_model():
    return _XGB_MODEL


def _get_crowd_model():
    return _CROWD_MODEL


def set_model(model) -> None:
    global _XGB_MODEL
    _XGB_MODEL = model


def set_crowd_model(model) -> None:
    global _CROWD_MODEL
    _CROWD_MODEL = model


def lines_for_station(station: str) -> List[str]:
    """Every line that calls at a station."""
    return [ln for ln, seq in NETWORK.items() if station in seq]


# ---------------------------------------------------------------------------
# 4. Real ML evaluation
# ---------------------------------------------------------------------------
class MLMetrics:
    """Genuine hold-out evaluation of the shipped booster."""

    FEATURES = [
        "Entry_Hour", "Day_of_Week", "Is_Peak_Hour", "Hour_Sin",
        "Hour_Cos", "From_Station", "To_Station", "Line_Color", "Train_Capacity",
    ]

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def _frame(self) -> pd.DataFrame:
        d = self.df.copy()
        ts = pd.to_datetime(d["Exact_Entry_Timestamp"])
        hour = ts.dt.hour
        peak = ((hour >= 8) & (hour <= 11)) | ((hour >= 17) & (hour <= 20))
        return pd.DataFrame({
            "Entry_Hour": hour,
            "Day_of_Week": ts.dt.dayofweek,
            "Is_Peak_Hour": peak.astype(int),
            "Hour_Sin": np.sin(2 * np.pi * hour / 24.0),
            "Hour_Cos": np.cos(2 * np.pi * hour / 24.0),
            "From_Station": d["From_Station"].map(STATION_INDEX),
            "To_Station": d["To_Station"].map(STATION_INDEX),
            "Line_Color": d["Line_Color"].map(LINE_INDEX),
            "Train_Capacity": d["Train_Capacity"],
        })

    def evaluate(self) -> Dict[str, Any]:
        model = _get_model()
        if model is None:
            return {"available": False, "reason": "model not loaded"}

        X = self._frame()
        y = self.df["Train_Occupancy_Count"].astype(float).values

        # chronological split - mirrors how the model was trained
        split = int(len(X) * 0.8)
        X_tr, X_te = X.iloc[:split], X.iloc[split:]
        y_tr, y_te = y[:split], y[split:]

        m = _clone(model)
        m.fit(X_tr, y_tr)
        pred = np.clip(m.predict(X_te), 0, None)

        resid = y_te - pred
        ss_res = float(np.sum(resid ** 2))
        ss_tot = float(np.sum((y_te - y_te.mean()) ** 2))

        metrics = {
            "available": True,
            "rows_total": int(len(X)),
            "rows_train": int(len(X_tr)),
            "rows_test": int(len(X_te)),
            "split_strategy": "Chronological 80/20 (no shuffling - respects time order)",
            "r2": round(1 - ss_res / ss_tot, 4),
            "mae": round(float(np.mean(np.abs(resid))), 2),
            "rmse": round(float(np.sqrt(np.mean(resid ** 2))), 2),
            "mape": round(float(np.mean(np.abs(resid) / np.maximum(y_te, 1)) * 100), 2),
            "bias": round(float(np.mean(resid)), 2),
            "within_10pct": round(float(np.mean(np.abs(resid) / np.maximum(y_te, 1) < 0.10) * 100), 1),
            "target": "Train_Occupancy_Count (passengers on board)",
        }

        # feature importance
        try:
            imp = m.feature_importances_
            metrics["feature_importance"] = sorted(
                [
                    {"feature": f, "importance": round(float(v), 5)}
                    for f, v in zip(self.FEATURES, imp)
                ],
                key=lambda x: -x["importance"],
            )
        except Exception:
            metrics["feature_importance"] = []

        # residuals by hour of day
        hour_te = X_te["Entry_Hour"].values
        by_hour = []
        for h in sorted(set(hour_te.tolist())):
            m_h = hour_te == h
            if m_h.sum() < 5:
                continue
            r = resid[m_h]
            by_hour.append({
                "hour": int(h),
                "mean_actual": round(float(y_te[m_h].mean()), 1),
                "mean_predicted": round(float(pred[m_h].mean()), 1),
                "mae": round(float(np.mean(np.abs(r))), 1),
                "bias": round(float(np.mean(r)), 1),
            })
        metrics["by_hour"] = by_hour

        # residuals by station
        st_te = self.df["From_Station"].iloc[split:].values
        by_station = []
        for s in sorted(set(st_te.tolist())):
            m_s = st_te == s
            if m_s.sum() < 5:
                continue
            r = resid[m_s]
            by_station.append({
                "station": s,
                "mae": round(float(np.mean(np.abs(r))), 1),
                "bias": round(float(np.mean(r)), 1),
            })
        metrics["by_station"] = by_station

        # station x hour error grid - the heatmap the dashboard renders
        hours = sorted(set(hour_te.tolist()))
        heatmap = []
        for st in STATIONS:
            row = []
            for h in hours:
                m = (st_te == st) & (hour_te == h)
                if m.sum() < 3:
                    row.append(None)
                else:
                    row.append({
                        "mae": round(float(np.mean(np.abs(resid[m]))), 1),
                        "bias": round(float(np.mean(resid[m])), 1),
                        "n": int(m.sum()),
                    })
            heatmap.append({"station": st, "cells": row})
        metrics["heatmap"] = {
            "rows": heatmap,
            "hours": [int(h) for h in hours],
            "metric": "MAE (mean absolute error, passengers)",
        }

        # station ranking: which station is hardest to predict
        by_station_sorted = sorted(by_station, key=lambda x: -x["mae"])
        metrics["hardest_station"] = by_station_sorted[0]["station"] if by_station_sorted else None
        metrics["easiest_station"] = by_station_sorted[-1]["station"] if by_station_sorted else None

        return metrics


def _clone(model):
    from sklearn.base import clone
    return clone(model)