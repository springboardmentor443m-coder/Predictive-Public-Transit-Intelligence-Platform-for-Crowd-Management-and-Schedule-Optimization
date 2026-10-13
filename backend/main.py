import asyncio
import datetime
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ml_model import G_LINE_STATIONS, get_schedule_period_data
import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI(title="MetroFlow G-Line Real-Time & Forecast Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app_asgi = socketio.ASGIApp(sio, app)

class ScheduleAdjustmentRequest(BaseModel):
    train_id: str
    new_delay_min: int
    new_headway_min: int

class ManualAlertRequest(BaseModel):
    title: str
    message: str
    severity: str
    target_station: str

class BroadcastAnnouncementRequest(BaseModel):
    message: str

class GLineFleetManager:
    def __init__(self):
        self.line_name = "G-Line (Brooklyn–Queens Crosstown)"
        self.stations = G_LINE_STATIONS
        self.headway_min = 8
        self.forecast_offset_min = 0
        self.alerts_list = []
        
        # Initialize 42 standard trains + 5 peak trains (47 total)
        self.trains = []
        for i in range(1, 48):
            direction = "Southbound" if i % 2 == 1 else "Northbound"
            station_idx = (i * 2) % len(self.stations)
            travel_timer = random.randint(5, 30)
            
            self.trains.append({
                "train_id": f"G-{100 + i}",
                "line": "G-Line",
                "station_idx": station_idx,
                "current_station": self.stations[station_idx],
                "next_station": self.stations[(station_idx + 1) % len(self.stations)],
                "direction": direction,
                "route": f"Court Sq ↔ Church Av ({direction})",
                "capacity": 1200,
                "passenger_count": random.randint(350, 1050),
                "speed_mph": random.randint(28, 42),
                "delay_min": 0,
                "scheduled_headway_min": self.headway_min,
                "seconds_to_arrival": travel_timer,
                "is_dwelling": False
            })
            
        self.station_performance = {}
        for station_name in self.stations:
            self.station_performance[station_name] = {
                "station_name": station_name,
                "trains_running": "Awaiting Train",
                "last_arrival_time": "No Recent Arrival",
                "avg_occupancy_pct": 0.0,
                "train_capacity": 1200,
                "crowd_density_pct": round(random.uniform(25.0, 50.0), 1),
                "inflow": 0,
                "outflow": 0,
                "status": "LOW DENSITY"
            }
            
        self.high_alert_station_count = 0
        self.add_alert("SYSTEM", "MetroFlow G-Line Engine Active with Future Forecasting.", "INFO")

    def add_alert(self, category: str, message: str, severity: str = "INFO"):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.alerts_list.insert(0, {
            "id": len(self.alerts_list) + 1,
            "category": category,
            "message": message,
            "severity": severity,
            "timestamp": now_str
        })
        self.alerts_list = self.alerts_list[:50]

    def tick_simulation_second(self):
        now_hour = datetime.datetime.now().hour
        period_info = get_schedule_period_data(now_hour)
        self.headway_min = period_info["recommended_headway_min"]
        active_limit = period_info["active_train_count"]

        base_travel_seconds = max(12, int(self.headway_min * 2.5))
        arrivals_this_tick = []

        for idx, train in enumerate(self.trains):
            if idx >= active_limit:
                continue

            train["scheduled_headway_min"] = self.headway_min
            train["seconds_to_arrival"] -= 1

            if train["seconds_to_arrival"] <= 0:
                if train["direction"] == "Southbound":
                    if train["station_idx"] < len(self.stations) - 1:
                        train["station_idx"] += 1
                    else:
                        train["direction"] = "Northbound"
                        train["station_idx"] -= 1
                else:
                    if train["station_idx"] > 0:
                        train["station_idx"] -= 1
                    else:
                        train["direction"] = "Southbound"
                        train["station_idx"] += 1

                arrived_station = self.stations[train["station_idx"]]
                train["current_station"] = arrived_station
                
                next_idx = (train["station_idx"] + 1) if train["direction"] == "Southbound" else (train["station_idx"] - 1)
                train["next_station"] = self.stations[next_idx % len(self.stations)]
                train["route"] = f"Court Sq ↔ Church Av ({train['direction']})"

                train["seconds_to_arrival"] = base_travel_seconds + (train["delay_min"] * 3)

                inflow = random.randint(110, 480)
                outflow = random.randint(90, 420)
                net_change = inflow - outflow
                train["passenger_count"] = min(max(train["passenger_count"] + net_change, 150), 1180)
                train["occupancy_pct"] = round((train["passenger_count"] / train["capacity"]) * 100, 1)

                occ_pct = train["occupancy_pct"]
                density_pct = round((inflow + outflow) / 10.0, 1)

                if occ_pct >= 80.0 or density_pct >= 80.0:
                    status = "HIGH ALERT"
                elif occ_pct >= 55.0 or density_pct >= 55.0:
                    status = "MODERATE"
                else:
                    status = "LOW DENSITY"

                arrival_time_str = datetime.datetime.now().strftime("%H:%M:%S")

                self.station_performance[arrived_station] = {
                    "station_name": arrived_station,
                    "trains_running": f"{train['train_id']} ({train['direction']})",
                    "last_arrival_time": arrival_time_str,
                    "avg_occupancy_pct": occ_pct,
                    "train_capacity": 1200,
                    "crowd_density_pct": density_pct,
                    "inflow": inflow,
                    "outflow": outflow,
                    "status": status
                }

                arrivals_this_tick.append(f"{train['train_id']} arrived at {arrived_station}")

        self.high_alert_station_count = sum(
            1 for s in self.station_performance.values() if s["status"] == "HIGH ALERT"
        )

        return arrivals_this_tick

    def adjust_train_schedule_and_cascade(self, target_train_id: str, new_delay_min: int, new_headway_min: int):
        found_idx = -1
        for idx, train in enumerate(self.trains):
            if train["train_id"] == target_train_id:
                found_idx = idx
                train["delay_min"] = new_delay_min
                train["scheduled_headway_min"] = new_headway_min
                train["seconds_to_arrival"] += (new_delay_min * 5)
                break

        if found_idx != -1:
            for i in range(1, 6):
                behind_idx = (found_idx + i) % len(self.trains)
                cascaded_delay = max(0, new_delay_min - i)
                self.trains[behind_idx]["delay_min"] = cascaded_delay
                self.trains[behind_idx]["scheduled_headway_min"] = new_headway_min
                self.trains[behind_idx]["seconds_to_arrival"] += (cascaded_delay * 3)

            self.add_alert(
                "SCHEDULE ADJUSTMENT",
                f"Train {target_train_id} schedule updated (+{new_delay_min}m delay). Cascaded delays to following 5 trains.",
                "WARNING"
            )

fleet_manager = GLineFleetManager()

async def stream_event_driven_loop():
    while True:
        await asyncio.sleep(1.0)
        arrivals = fleet_manager.tick_simulation_second()
        
        now_hour = datetime.datetime.now().hour
        period_info = get_schedule_period_data(now_hour)
        station_list = [fleet_manager.station_performance[name] for name in fleet_manager.stations]

        payload = {
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "is_forecast": False,
            "line_name": fleet_manager.line_name,
            "total_stations": len(G_LINE_STATIONS),
            "active_train_count": period_info["active_train_count"],
            "high_alert_stations": fleet_manager.high_alert_station_count,
            "period_info": period_info,
            "forecast_offset_min": 0,
            "trains": fleet_manager.trains,
            "station_performance": station_list,
            "alerts": fleet_manager.alerts_list,
            "recent_arrivals": arrivals
        }
        await sio.emit("live_fleet_update", payload)

@app.on_event("startup")
async def start_streaming():
    asyncio.create_task(stream_event_driven_loop())

@app.get("/api/forecast/{offset_min}")
def get_future_forecast(offset_min: int):
    """Generates projected future fleet and station telemetry for +offset_min minutes into the future."""
    future_time = datetime.datetime.now() + datetime.timedelta(minutes=offset_min)
    future_hour = future_time.hour
    
    period_info = get_schedule_period_data(future_hour)
    headway = period_info["recommended_headway_min"]
    active_limit = period_info["active_train_count"]

    # Calculate train movement hops
    station_hops = max(1, offset_min // 2)

    forecasted_trains = []
    forecasted_stations = {}

    for idx, train in enumerate(fleet_manager.trains):
        if idx >= active_limit:
            continue

        s_idx = train["station_idx"]
        direction = train["direction"]

        for _ in range(station_hops):
            if direction == "Southbound":
                if s_idx < len(G_LINE_STATIONS) - 1:
                    s_idx += 1
                else:
                    direction = "Northbound"
                    s_idx -= 1
            else:
                if s_idx > 0:
                    s_idx -= 1
                else:
                    direction = "Southbound"
                    s_idx += 1

        curr_station = G_LINE_STATIONS[s_idx]
        next_idx = (s_idx + 1) if direction == "Southbound" else (s_idx - 1)
        next_station = G_LINE_STATIONS[next_idx % len(G_LINE_STATIONS)]

        base_future_occ = period_info["predicted_occupancy_pct"]
        proj_occ = round(min(max(base_future_occ + random.uniform(-8, 8), 15.0), 98.0), 1)
        proj_passengers = int((proj_occ / 100.0) * 1200)

        forecasted_trains.append({
            "train_id": train["train_id"],
            "line": "G-Line",
            "station_idx": s_idx,
            "current_station": curr_station,
            "next_station": next_station,
            "direction": direction,
            "route": f"Court Sq ↔ Church Av ({direction})",
            "capacity": 1200,
            "passenger_count": proj_passengers,
            "occupancy_pct": proj_occ,
            "speed_mph": random.randint(30, 44),
            "delay_min": max(0, train["delay_min"] - (offset_min // 5)),
            "scheduled_headway_min": headway,
            "seconds_to_arrival": 30
        })

    high_alert_count = 0
    for s_name in G_LINE_STATIONS:
        serving = [t for t in forecasted_trains if t["current_station"] == s_name]
        if serving:
            avg_occ = sum(t["occupancy_pct"] for t in serving) / len(serving)
            t_str = ", ".join([t["train_id"] for t in serving])
        else:
            avg_occ = round(min(max(period_info["predicted_occupancy_pct"] + random.uniform(-10, 10), 20.0), 95.0), 1)
            t_str = "In Transit"

        inflow = random.randint(150, 520)
        outflow = random.randint(120, 480)
        density_pct = round((inflow + outflow) / 10.0, 1)

        if avg_occ >= 80.0 or density_pct >= 80.0:
            status = "HIGH ALERT"
            high_alert_count += 1
        elif avg_occ >= 55.0 or density_pct >= 55.0:
            status = "MODERATE"
        else:
            status = "LOW DENSITY"

        forecasted_stations[s_name] = {
            "station_name": s_name,
            "trains_running": t_str,
            "last_arrival_time": f"Projected {future_time.strftime('%H:%M:%S')}",
            "avg_occupancy_pct": avg_occ,
            "train_capacity": 1200,
            "crowd_density_pct": density_pct,
            "inflow": inflow,
            "outflow": outflow,
            "status": status
        }

    station_list = [forecasted_stations[name] for name in G_LINE_STATIONS]

    return {
        "timestamp": f"FORECAST (+{offset_min}m) for {future_time.strftime('%H:%M:%S')}",
        "is_forecast": True,
        "line_name": fleet_manager.line_name,
        "total_stations": len(G_LINE_STATIONS),
        "active_train_count": len(forecasted_trains),
        "high_alert_stations": high_alert_count,
        "period_info": period_info,
        "forecast_offset_min": offset_min,
        "trains": forecasted_trains,
        "station_performance": station_list,
        "alerts": fleet_manager.alerts_list,
        "recent_arrivals": [f"Forecast projected for +{offset_min} minutes"]
    }

@app.post("/api/schedule/adjust-train")
def adjust_train(req: ScheduleAdjustmentRequest):
    fleet_manager.adjust_train_schedule_and_cascade(req.train_id, req.new_delay_min, req.new_headway_min)
    return {"status": "SUCCESS", "message": f"Updated {req.train_id} and cascaded schedule changes to trailing fleet."}

@app.post("/api/alerts/broadcast")
def broadcast_alert(req: BroadcastAnnouncementRequest):
    fleet_manager.add_alert("ANNOUNCEMENT", req.message, "HIGH")
    return {"status": "SUCCESS", "message": "Broadcast announcement published."}

@app.post("/api/alerts/manual")
def manual_alert(req: ManualAlertRequest):
    fleet_manager.add_alert(
        f"STATION ALERT ({req.target_station})",
        f"{req.title}: {req.message}",
        req.severity
    )
    return {"status": "SUCCESS", "message": "Manual alert created."}

@app.get("/api/analysis/daily/{day_of_month}")
def get_daily_analysis(day_of_month: int):
    random.seed(day_of_month * 100)
    avg_density = round(random.uniform(45.0, 88.0), 1)
    delay_freq = round(random.uniform(2.1, 8.5), 1)
    throughput = random.randint(180000, 310000)

    hourly_curve = []
    for h in range(24):
        if 7 <= h <= 9 or 17 <= h <= 19:
            val = random.randint(75, 98)
        elif 10 <= h <= 16:
            val = random.randint(48, 70)
        else:
            val = random.randint(18, 45)
        hourly_curve.append({"hour": f"{h:02d}:00", "density": val})

    station_breakdown = [
        {"station": s, "throughput": random.randint(8000, 18000), "delays": random.randint(0, 6)}
        for s in G_LINE_STATIONS[:10]
    ]

    return {
        "selected_day": day_of_month,
        "kpis": {
            "avg_crowd_density_pct": avg_density,
            "delay_frequency_per_hr": delay_freq,
            "daily_throughput_passengers": throughput
        },
        "hourly_density": hourly_curve,
        "station_breakdown": station_breakdown
    }

@app.get("/api/health")
def health_check():
    return {"status": "G-Line Engine Active"}