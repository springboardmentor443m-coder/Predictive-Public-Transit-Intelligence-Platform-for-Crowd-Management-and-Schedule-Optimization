"""
MetroFlow Real-Time Simulation Engine
Simulates live GPS train telemetry, passenger turnstile tap-in/tap-out telemetry,
platform dwell dynamics, and cascading congestion across New York City subway network.
"""

import math
import random
import time
import asyncio
from typing import Dict, List, Any
from data.nyc_subway_data import NYC_STATIONS, NYC_SUBWAY_LINES, LINE_ROUTES
from ml.forecasting_engine import forecaster

class LiveMetroSimulation:
    def __init__(self):
        self.stations_data: Dict[str, Dict[str, Any]] = {}
        self.trains_data: List[Dict[str, Any]] = []
        self.history_samples: Dict[str, List[Dict[str, Any]]] = {}
        self.last_update_ts = time.time()
        self.is_running = False
        self._init_state()

    def _init_state(self):
        # Initialize station states
        now = time.time()
        for s in NYC_STATIONS:
            sid = s["id"]
            # Start around 40-75% capacity with realistic base
            base_occ = int(s["platform_capacity"] * random.uniform(0.42, 0.72))
            density = round((base_occ / s["platform_capacity"]) * 100, 1)
            
            self.stations_data[sid] = {
                "id": sid,
                "name": s["name"],
                "borough": s["borough"],
                "lat": s["lat"],
                "lon": s["lon"],
                "lines": s["lines"],
                "zone": s["zone"],
                "capacity": s["platform_capacity"],
                "current_occupancy": base_occ,
                "density_percent": density,
                "congestion_level": self._classify_congestion(density),
                "inflow_rate": int(s["base_inflow_rate"] * random.uniform(0.85, 1.15)),
                "outflow_rate": int(s["base_outflow_rate"] * random.uniform(0.85, 1.15)),
                "turnstiles": s["turnstiles"],
                "turnstiles_active": s["turnstiles"],
                "trend": "steady",
                "last_train_arrival": "2m ago"
            }

            # Seed 10-point historical sparkline
            self.history_samples[sid] = []
            for i in range(12):
                hist_density = max(10.0, min(100.0, density + random.uniform(-6, 6)))
                self.history_samples[sid].append({
                    "time": time.strftime("%H:%M", time.localtime(now - (12 - i) * 60)),
                    "density": round(hist_density, 1),
                    "inflow": int(s["base_inflow_rate"] * (hist_density / 50.0)),
                    "outflow": int(s["base_outflow_rate"] * (hist_density / 50.0))
                })

        # Initialize Active Trains on different subway lines
        train_configs = [
            {"id": "TR-101", "line": "1", "route_idx": 1, "progress": 45, "dir": 1},
            {"id": "TR-102", "line": "1", "route_idx": 3, "progress": 80, "dir": -1},
            {"id": "TR-201", "line": "2", "route_idx": 2, "progress": 20, "dir": 1},
            {"id": "TR-401", "line": "4", "route_idx": 2, "progress": 60, "dir": 1},
            {"id": "TR-402", "line": "4", "route_idx": 4, "progress": 15, "dir": -1},
            {"id": "TR-601", "line": "6", "route_idx": 1, "progress": 70, "dir": 1},
            {"id": "TR-701", "line": "7", "route_idx": 1, "progress": 35, "dir": 1},
            {"id": "TR-702", "line": "7", "route_idx": 3, "progress": 90, "dir": -1},
            {"id": "TR-A01", "line": "A", "route_idx": 1, "progress": 50, "dir": 1},
            {"id": "TR-A02", "line": "A", "route_idx": 2, "progress": 25, "dir": -1},
            {"id": "TR-E01", "line": "E", "route_idx": 2, "progress": 65, "dir": 1},
            {"id": "TR-L01", "line": "L", "route_idx": 0, "progress": 40, "dir": 1},
            {"id": "TR-N01", "line": "N", "route_idx": 2, "progress": 10, "dir": 1},
            {"id": "TR-Q01", "line": "Q", "route_idx": 3, "progress": 85, "dir": -1},
        ]

        station_lookup = {s["id"]: s for s in NYC_STATIONS}
        for cfg in train_configs:
            route = LINE_ROUTES.get(cfg["line"], ["NYC-TSQ42", "NYC-PENN34"])
            from_st = station_lookup[route[cfg["route_idx"]]]
            next_idx = min(len(route) - 1, cfg["route_idx"] + 1)
            to_st = station_lookup[route[next_idx]]

            # GPS interpolation
            pct = cfg["progress"] / 100.0
            lat = from_st["lat"] + (to_st["lat"] - from_st["lat"]) * pct
            lon = from_st["lon"] + (to_st["lon"] - from_st["lon"]) * pct

            self.trains_data.append({
                "id": cfg["id"],
                "line": cfg["line"],
                "line_name": NYC_SUBWAY_LINES[cfg["line"]]["name"],
                "line_color": NYC_SUBWAY_LINES[cfg["line"]]["color"],
                "from_station_id": from_st["id"],
                "from_station_name": from_st["name"],
                "to_station_id": to_st["id"],
                "to_station_name": to_st["name"],
                "route_idx": cfg["route_idx"],
                "direction": cfg["dir"],
                "progress": cfg["progress"],
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "speed_mph": random.randint(24, 38),
                "occupancy_percent": random.randint(45, 82),
                "cars": 8,
                "delay_seconds": random.choice([0, 0, 15, 30, 90]),
                "status": "In Transit"
            })

    def _classify_congestion(self, density_pct: float) -> str:
        if density_pct >= 85:
            return "Severe"
        elif density_pct >= 70:
            return "High"
        elif density_pct >= 45:
            return "Moderate"
        return "Low"

    def tick_simulation(self):
        """Advances simulation by 1 step (simulates real-world turnstile & train progression)."""
        now = time.time()
        station_lookup = {s["id"]: s for s in NYC_STATIONS}

        # 1. Update station turnstile flow & passenger loading
        for sid, s in self.stations_data.items():
            # Stochastic fluctuation
            delta_in = random.randint(-25, 30)
            delta_out = random.randint(-25, 28)
            s["inflow_rate"] = max(20, s["inflow_rate"] + delta_in)
            s["outflow_rate"] = max(20, s["outflow_rate"] + delta_out)

            # Net platform occupancy change
            net_change = (s["inflow_rate"] - s["outflow_rate"]) // 4
            new_occ = max(100, min(s["capacity"], s["current_occupancy"] + net_change))
            
            old_density = s["density_percent"]
            new_density = round((new_occ / s["capacity"]) * 100, 1)
            
            s["current_occupancy"] = new_occ
            s["density_percent"] = new_density
            s["congestion_level"] = self._classify_congestion(new_density)

            if new_density > old_density + 0.5:
                s["trend"] = "rising"
            elif new_density < old_density - 0.5:
                s["trend"] = "falling"
            else:
                s["trend"] = "steady"

        # 2. Advance train positions along subway lines
        for tr in self.trains_data:
            route = LINE_ROUTES.get(tr["line"], ["NYC-TSQ42", "NYC-PENN34"])
            max_idx = len(route) - 1
            
            # Progress train
            step = random.uniform(3.5, 7.0)
            tr["progress"] += step

            if tr["progress"] >= 100:
                # Arrived at next station
                tr["progress"] = 0
                current_idx = tr["route_idx"]
                
                # Check direction bounce or loop
                if tr["direction"] == 1:
                    if current_idx + 1 >= max_idx:
                        tr["direction"] = -1
                        tr["route_idx"] = max_idx
                    else:
                        tr["route_idx"] = current_idx + 1
                else:
                    if current_idx - 1 <= 0:
                        tr["direction"] = 1
                        tr["route_idx"] = 0
                    else:
                        tr["route_idx"] = current_idx - 1

                from_sid = route[tr["route_idx"]]
                next_offset = 1 if tr["direction"] == 1 else -1
                next_idx = max(0, min(max_idx, tr["route_idx"] + next_offset))
                to_sid = route[next_idx]

                from_st = station_lookup.get(from_sid, NYC_STATIONS[0])
                to_st = station_lookup.get(to_sid, NYC_STATIONS[1])

                tr["from_station_id"] = from_st["id"]
                tr["from_station_name"] = from_st["name"]
                tr["to_station_id"] = to_st["id"]
                tr["to_station_name"] = to_st["name"]
                tr["occupancy_percent"] = max(20, min(98, tr["occupancy_percent"] + random.randint(-15, 18)))
                tr["speed_mph"] = random.randint(26, 42)
                tr["status"] = "Station Dwell"
            else:
                tr["status"] = "In Transit"

            # Interpolate coordinates
            from_st = station_lookup.get(tr["from_station_id"], NYC_STATIONS[0])
            to_st = station_lookup.get(tr["to_station_id"], NYC_STATIONS[1])
            pct = tr["progress"] / 100.0
            tr["lat"] = round(from_st["lat"] + (to_st["lat"] - from_st["lat"]) * pct, 6)
            tr["lon"] = round(from_st["lon"] + (to_st["lon"] - from_st["lon"]) * pct, 6)

        self.last_update_ts = now

    def get_full_snapshot(self) -> Dict[str, Any]:
        """Returns instantaneous network state snapshot."""
        stations_list = list(self.stations_data.values())
        
        # Calculate network aggregate metrics
        total_passengers = sum(s["current_occupancy"] for s in stations_list)
        total_capacity = sum(s["capacity"] for s in stations_list)
        network_density = round((total_passengers / total_capacity) * 100, 1) if total_capacity > 0 else 0
        total_inflow = sum(s["inflow_rate"] for s in stations_list)
        total_outflow = sum(s["outflow_rate"] for s in stations_list)
        
        severe_count = sum(1 for s in stations_list if s["congestion_level"] == "Severe")
        high_count = sum(1 for s in stations_list if s["congestion_level"] == "High")
        moderate_count = sum(1 for s in stations_list if s["congestion_level"] == "Moderate")
        normal_count = sum(1 for s in stations_list if s["congestion_level"] == "Low")

        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "network_metrics": {
                "active_network_passengers": total_passengers,
                "network_capacity": total_capacity,
                "overall_density_percent": network_density,
                "total_inflow_rate": total_inflow,
                "total_outflow_rate": total_outflow,
                "active_trains_count": len(self.trains_data),
                "stations_monitored": len(stations_list),
                "severe_congestion_stations": severe_count,
                "high_congestion_stations": high_count,
                "moderate_congestion_stations": moderate_count,
                "normal_stations": normal_count,
                "system_status": "Heavy Flow - Optimal Headways" if severe_count > 0 else "Normal Transit Operations"
            },
            "stations": stations_list,
            "trains": self.trains_data
        }

# Global simulator instance
simulator = LiveMetroSimulation()
