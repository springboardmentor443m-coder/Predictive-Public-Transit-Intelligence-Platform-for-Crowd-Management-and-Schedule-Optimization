"""
AI MetroFlow - Live Train Tracking & Real-Time Transit Simulator Engine
Manages realistic kinematics, route sequences, and telemetry for NYC subway trains.
"""

import os
import math
import time
import random
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import numpy as np


# Route display configuration with official MTA route branding
ROUTE_CONFIG = {
    "1": {"name": "Broadway - 7 Av Local", "color": "#EE352E", "line": "Broadway-7th"},
    "4": {"name": "Lexington Av Express", "color": "#00933C", "line": "Lexington"},
    "6": {"name": "Lexington Av Local", "color": "#00933C", "line": "Lexington"},
    "7": {"name": "Flushing Local / Express", "color": "#B933AD", "line": "Flushing"},
    "A": {"name": "8th Av Express", "color": "#0039A6", "line": "Eighth"},
    "E": {"name": "8th Av / Queens Blvd Local", "color": "#0039A6", "line": "Eighth"},
    "L": {"name": "14th St - Canarsie Local", "color": "#A7A9AC", "line": "Canarsie"},
    "N": {"name": "Broadway Express", "color": "#FCCC0A", "line": "Broadway"},
}

# Sequenced station corridors for each active subway route
DEFAULT_ROUTE_STOPS = {
    "1": [
        "Van Cortlandt Park - 242 St", "238 St", "231 St", "125 St", "116 St",
        "103 St", "Times Sq - 42 St", "34 St - Penn Station", "14 St", "Canal St", "Cortlandt St"
    ],
    "4": [
        "Woodlawn", "Bedford Park Blvd", "149 St - Grand Concourse", "125 St", "86 St",
        "Grand Central - 42 St", "14 St - Union Sq", "Fulton St", "Atlantic Av - Barclays Ctr"
    ],
    "6": [
        "Pelham Bay Park", "Parkchester", "Hunts Point Av", "125 St", "86 St",
        "68 St - Hunter College", "Grand Central - 42 St", "14 St - Union Sq", "Canal St", "Brooklyn Bridge - City Hall"
    ],
    "7": [
        "Flushing - Main St", "Mets - Willets Point", "Junction Blvd", "74 St - Broadway",
        "Woodside - 61 St", "Queensboro Plaza", "Court Sq", "Grand Central - 42 St", "Times Sq - 42 St"
    ],
    "A": [
        "Inwood - 207 St", "168 St", "145 St", "125 St", "59 St - Columbus Circle",
        "42 St - Port Authority Bus Terminal", "34 St - Penn Station", "14 St", "Fulton St",
        "Jay St - MetroTech", "Broadway Jct", "Euclid Av"
    ],
    "E": [
        "Jamaica Center - Parsons/Archer", "Forest Hills - 71 Av", "Jackson Hts - Roosevelt Av",
        "Queens Plaza", "Court Sq", "Lexington Av/59 St", "50 St",
        "42 St - Port Authority Bus Terminal", "34 St - Penn Station", "Cortlandt St"
    ],
    "L": [
        "8 Av", "6 Av", "14 St - Union Sq", "3 Av", "1 Av",
        "Bedford Av", "Lorimer St", "Myrtle - Wyckoff Avs", "Broadway Jct", "Canarsie - Rockaway Pkwy"
    ],
    "N": [
        "Astoria - Ditmars Blvd", "Astoria Blvd", "Queensboro Plaza", "Lexington Av/59 St",
        "Times Sq - 42 St", "14 St - Union Sq", "Canal St", "Atlantic Av - Barclays Ctr",
        "36 St", "Coney Island - Stillwell Av"
    ],
}


def haversine_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in miles."""
    r = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return max(r * c, 0.05)


class SimulatedTrain:
    """Represents a single active subway train running along a route."""

    def __init__(
        self,
        train_id: str,
        route: str,
        route_stations: List[Dict[str, Any]],
        initial_leg_idx: int = 0,
        initial_progress: float = 0.0,
        direction: str = "Southbound",
        status: str = "On Time",
        delay_minutes: float = 0.0,
    ):
        self.train_id = train_id
        self.route = route
        self.route_stations = route_stations
        self.num_stops = len(route_stations)
        self.leg_idx = max(0, min(initial_leg_idx, self.num_stops - 2))
        self.progress = float(initial_progress)  # 0.0 to 1.0 along current leg
        self.direction = direction  # "Southbound" (forward) or "Northbound" (reversed)
        self.status = status  # "On Time", "Delayed", "Arriving", "Departed"
        self.delay_minutes = float(delay_minutes)
        self.speed_mph = random.uniform(26.0, 38.0)
        self.lat = 40.7500
        self.lon = -73.9800
        self.current_station = ""
        self.next_station = ""
        self.update_coordinates()

    def get_endpoints(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Returns the origin and destination station dictionaries for the active leg."""
        if self.direction == "Southbound":
            origin = self.route_stations[self.leg_idx]
            destination = self.route_stations[self.leg_idx + 1]
        else:
            rev_idx = (self.num_stops - 1) - self.leg_idx
            origin = self.route_stations[rev_idx]
            destination = self.route_stations[rev_idx - 1]
        return origin, destination

    def update_coordinates(self):
        """Linearly interpolates GPS coordinates based on segment progress."""
        origin, destination = self.get_endpoints()
        self.current_station = origin["Stop Name"]
        self.next_station = destination["Stop Name"]

        lat1, lon1 = origin["Latitude"], origin["Longitude"]
        lat2, lon2 = destination["Latitude"], destination["Longitude"]

        # Smooth cubic ease for natural acceleration/deceleration kinematics
        p = self.progress
        self.lat = lat1 + (lat2 - lat1) * p
        self.lon = lon1 + (lon2 - lon1) * p

        # Realistic subway speed curve based on segment progress
        if self.status == "Delayed":
            self.speed_mph = max(8.0, 18.0 + random.uniform(-4.0, 4.0))
        elif p < 0.15:
            # Accelerating out of station
            self.speed_mph = 12.0 + (p / 0.15) * 18.0 + random.uniform(-2.0, 2.0)
            if self.delay_minutes < 2.0:
                self.status = "Departed"
        elif p > 0.82:
            # Decelerating into upcoming station
            self.speed_mph = 10.0 + ((1.0 - p) / 0.18) * 16.0 + random.uniform(-2.0, 2.0)
            if self.delay_minutes < 2.0:
                self.status = "Arriving"
        else:
            # Cruising speed in tunnels
            self.speed_mph = 32.0 + random.uniform(-3.0, 6.0)
            if self.delay_minutes < 2.0:
                self.status = "On Time"

        self.speed_mph = round(max(0.0, min(self.speed_mph, 48.0)), 1)

    def advance(self, delta_seconds: float = 3.0):
        """Advances train along its route based on elapsed delta seconds."""
        origin, destination = self.get_endpoints()
        distance_miles = haversine_distance_miles(
            origin["Latitude"], origin["Longitude"],
            destination["Latitude"], destination["Longitude"]
        )

        # Distance covered in miles = (speed in mph * delta_seconds / 3600)
        # Apply slight speed-up multiplier for dynamic dashboard visual engagement (3x time scale)
        distance_traveled = (self.speed_mph * (delta_seconds * 3.5)) / 3600.0
        delta_progress = distance_traveled / max(distance_miles, 0.05)

        self.progress += delta_progress

        # Stochastic minor delay evolution
        if random.random() < 0.03:
            if self.delay_minutes > 0.5:
                self.delay_minutes = max(0.0, self.delay_minutes - random.uniform(0.5, 1.2))
            elif random.random() < 0.2:
                self.delay_minutes += random.uniform(1.0, 3.5)

        if self.delay_minutes >= 3.0:
            self.status = "Delayed"

        # Check if train arrived at destination station
        if self.progress >= 1.0:
            self.progress = 0.0
            self.leg_idx += 1

            # End of corridor reached -> reverse direction
            if self.leg_idx >= self.num_stops - 1:
                self.leg_idx = 0
                self.direction = "Northbound" if self.direction == "Southbound" else "Southbound"

        self.update_coordinates()


class TrainFleetSimulator:
    """
    Fleet simulation manager for the NYC subway network.
    Maintains synchronized state across 24-32 active trains running in real-time.
    """

    def __init__(self, stations_csv: Optional[str] = None):
        self.stations_csv = stations_csv or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "stations.csv"
        )
        self.stations_df = self._load_stations()
        self.station_lookup = self._build_lookup()
        self.routes_data = self._build_routes()
        self.trains: List[SimulatedTrain] = []
        self._init_fleet()
        self.last_update_ts = time.time()

    def _load_stations(self) -> pd.DataFrame:
        """Loads station coordinates."""
        if os.path.exists(self.stations_csv):
            try:
                return pd.read_csv(self.stations_csv)
            except Exception:
                pass
        return pd.DataFrame()

    def _build_lookup(self) -> Dict[str, Dict[str, Any]]:
        """Maps Stop Name to station attributes."""
        lookup = {}
        if not self.stations_df.empty:
            for _, row in self.stations_df.iterrows():
                lookup[row["Stop Name"]] = {
                    "Stop Name": row["Stop Name"],
                    "Borough": row.get("Borough", "Manhattan"),
                    "Structure": row.get("Structure", "Subway"),
                    "Latitude": float(row["Latitude"]),
                    "Longitude": float(row["Longitude"]),
                }
        return lookup

    def _build_routes(self) -> Dict[str, List[Dict[str, Any]]]:
        """Constructs ordered lists of stations for each subway line."""
        routes = {}
        for r_id, stop_names in DEFAULT_ROUTE_STOPS.items():
            valid_stops = []
            for s_name in stop_names:
                if s_name in self.station_lookup:
                    valid_stops.append(self.station_lookup[s_name])
            if len(valid_stops) >= 3:
                routes[r_id] = valid_stops
        return routes

    def _init_fleet(self):
        """Initializes a fleet of realistic subway trains across all routes."""
        self.trains.clear()

        # Distribution of trains per route
        fleet_manifest = [
            # Line 1 (Broadway)
            {"id": "TR-101", "route": "1", "leg": 1, "prog": 0.2, "dir": "Southbound", "status": "On Time", "delay": 0.0},
            {"id": "TR-102", "route": "1", "leg": 4, "prog": 0.6, "dir": "Southbound", "status": "On Time", "delay": 0.5},
            {"id": "TR-103", "route": "1", "leg": 2, "prog": 0.8, "dir": "Northbound", "status": "Delayed", "delay": 4.5},
            {"id": "TR-104", "route": "1", "leg": 6, "prog": 0.1, "dir": "Northbound", "status": "Departed", "delay": 0.0},

            # Line 4 (Lexington Express)
            {"id": "TR-401", "route": "4", "leg": 2, "prog": 0.5, "dir": "Southbound", "status": "On Time", "delay": 0.0},
            {"id": "TR-402", "route": "4", "leg": 4, "prog": 0.85, "dir": "Southbound", "status": "Arriving", "delay": 0.0},
            {"id": "TR-403", "route": "4", "leg": 1, "prog": 0.4, "dir": "Northbound", "status": "Delayed", "delay": 5.2},
            {"id": "TR-404", "route": "4", "leg": 5, "prog": 0.2, "dir": "Northbound", "status": "On Time", "delay": 1.0},

            # Line 6 (Lexington Local)
            {"id": "TR-601", "route": "6", "leg": 2, "prog": 0.3, "dir": "Southbound", "status": "On Time", "delay": 0.0},
            {"id": "TR-602", "route": "6", "leg": 5, "prog": 0.7, "dir": "Southbound", "status": "On Time", "delay": 0.0},
            {"id": "TR-603", "route": "6", "leg": 3, "prog": 0.1, "dir": "Northbound", "status": "Departed", "delay": 0.0},

            # Line 7 (Flushing)
            {"id": "TR-701", "route": "7", "leg": 1, "prog": 0.4, "dir": "Southbound", "status": "On Time", "delay": 0.0},
            {"id": "TR-702", "route": "7", "leg": 4, "prog": 0.88, "dir": "Southbound", "status": "Arriving", "delay": 0.0},
            {"id": "TR-703", "route": "7", "leg": 2, "prog": 0.25, "dir": "Northbound", "status": "Delayed", "delay": 3.8},
            {"id": "TR-704", "route": "7", "leg": 5, "prog": 0.6, "dir": "Northbound", "status": "On Time", "delay": 0.0},

            # Line A (8th Av Express)
            {"id": "TR-A01", "route": "A", "leg": 2, "prog": 0.3, "dir": "Southbound", "status": "On Time", "delay": 0.0},
            {"id": "TR-A02", "route": "A", "leg": 5, "prog": 0.75, "dir": "Southbound", "status": "On Time", "delay": 1.2},
            {"id": "TR-A03", "route": "A", "leg": 8, "prog": 0.85, "dir": "Southbound", "status": "Arriving", "delay": 0.0},
            {"id": "TR-A04", "route": "A", "leg": 3, "prog": 0.2, "dir": "Northbound", "status": "Delayed", "delay": 6.0},

            # Line E (Queens Blvd / 8th Av)
            {"id": "TR-E01", "route": "E", "leg": 2, "prog": 0.4, "dir": "Southbound", "status": "On Time", "delay": 0.0},
            {"id": "TR-E02", "route": "E", "leg": 5, "prog": 0.9, "dir": "Southbound", "status": "Arriving", "delay": 0.0},
            {"id": "TR-E03", "route": "E", "leg": 3, "prog": 0.1, "dir": "Northbound", "status": "Departed", "delay": 0.0},

            # Line L (Canarsie)
            {"id": "TR-L01", "route": "L", "leg": 1, "prog": 0.5, "dir": "Southbound", "status": "On Time", "delay": 0.0},
            {"id": "TR-L02", "route": "L", "leg": 4, "prog": 0.85, "dir": "Southbound", "status": "Arriving", "delay": 0.0},
            {"id": "TR-L03", "route": "L", "leg": 2, "prog": 0.3, "dir": "Northbound", "status": "Delayed", "delay": 4.1},

            # Line N (Broadway Express)
            {"id": "TR-N01", "route": "N", "leg": 2, "prog": 0.6, "dir": "Southbound", "status": "On Time", "delay": 0.0},
            {"id": "TR-N02", "route": "N", "leg": 5, "prog": 0.3, "dir": "Southbound", "status": "On Time", "delay": 0.0},
            {"id": "TR-N03", "route": "N", "leg": 2, "prog": 0.1, "dir": "Northbound", "status": "Departed", "delay": 0.0},
            {"id": "TR-N04", "route": "N", "leg": 6, "prog": 0.7, "dir": "Northbound", "status": "Delayed", "delay": 3.5},
        ]

        for item in fleet_manifest:
            r_id = item["route"]
            if r_id in self.routes_data:
                train = SimulatedTrain(
                    train_id=item["id"],
                    route=r_id,
                    route_stations=self.routes_data[r_id],
                    initial_leg_idx=item["leg"],
                    initial_progress=item["prog"],
                    direction=item["dir"],
                    status=item["status"],
                    delay_minutes=item["delay"],
                )
                self.trains.append(train)

    def step(self, delta_seconds: float = 3.0):
        """Advances positions of all active trains in the fleet."""
        for train in self.trains:
            train.advance(delta_seconds=delta_seconds)
        self.last_update_ts = time.time()

    def inject_delay(self, train_id: str, delay_minutes: float = 5.0):
        """Injects a specific operational delay to a train for incident simulation."""
        for train in self.trains:
            if train.train_id == train_id:
                train.delay_minutes = delay_minutes
                train.status = "Delayed"
                train.update_coordinates()
                break

    def get_fleet_dataframe(self) -> pd.DataFrame:
        """
        Exports real-time fleet telemetry as a formatted pandas DataFrame.
        Includes Train ID, Route, Coordinates, Speed, Status, Current/Next Station.
        """
        records = []
        for t in self.trains:
            cfg = ROUTE_CONFIG.get(t.route, {"name": f"Line {t.route}", "color": "#2563EB", "line": "Subway"})
            records.append({
                "Train ID": t.train_id,
                "Route": t.route,
                "Route Name": cfg["name"],
                "Line Group": cfg["line"],
                "Current Latitude": t.lat,
                "Current Longitude": t.lon,
                "Speed (mph)": t.speed_mph,
                "Status": t.status,
                "Current Station": t.current_station,
                "Next Station": t.next_station,
                "Delay (min)": round(t.delay_minutes, 1),
                "Direction": t.direction,
                "Route Color": cfg["color"],
                "Segment Progress": round(t.progress, 2),
            })
        return pd.DataFrame(records)

    def get_route_trajectories(self) -> Dict[str, Dict[str, Any]]:
        """Returns geographic lines for all active subway routes for map track rendering."""
        trajectories = {}
        for r_id, stops in self.routes_data.items():
            cfg = ROUTE_CONFIG.get(r_id, {"name": f"Line {r_id}", "color": "#2563EB"})
            lats = [s["Latitude"] for s in stops]
            lons = [s["Longitude"] for s in stops]
            names = [s["Stop Name"] for s in stops]
            trajectories[r_id] = {
                "route": r_id,
                "name": cfg["name"],
                "color": cfg["color"],
                "lats": lats,
                "lons": lons,
                "stops": names,
            }
        return trajectories

    def get_fleet_kpis(self) -> Dict[str, Any]:
        """Calculates top-level operational fleet metrics."""
        total = len(self.trains)
        delayed = sum(1 for t in self.trains if t.status == "Delayed")
        on_time = sum(1 for t in self.trains if t.status in ["On Time", "Arriving", "Departed"])
        speeds = [t.speed_mph for t in self.trains]
        avg_speed = round(float(np.mean(speeds)), 1) if speeds else 0.0

        return {
            "active_trains": total,
            "delayed_trains": delayed,
            "ontime_trains": on_time,
            "avg_speed": avg_speed,
            "on_time_pct": round((on_time / max(total, 1)) * 100, 1),
            "delayed_pct": round((delayed / max(total, 1)) * 100, 1),
        }
