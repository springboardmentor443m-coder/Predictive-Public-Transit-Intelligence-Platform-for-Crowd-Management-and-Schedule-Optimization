from fastapi import APIRouter

router = APIRouter(prefix="/api/network", tags=["Network"])

@router.get("/map")
def get_network_map():
    return {
        "lines": [
            {
                "id": "blue-line",
                "name": "Blue Corridor",
                "color": "#38bdf8",
                "path": "M 80 180 L 260 180 L 440 280 L 640 280 L 820 400 L 980 400"
            },
            {
                "id": "emerald-line",
                "name": "Emerald Express",
                "color": "#34d399",
                "path": "M 120 480 L 320 480 L 440 280 L 640 280 L 760 140 L 940 140"
            },
            {
                "id": "ruby-line",
                "name": "Ruby Loop",
                "color": "#fb7185",
                "path": "M 260 180 L 320 480 L 540 540 L 820 400"
            }
        ],
        "stations": [
            {
                "id": "ST-01",
                "name": "Central Terminal",
                "x": 80,
                "y": 180,
                "line": "Blue Corridor",
                "occupancy_pct": 74,
                "status": "ELEVATED",
                "inflow_rate": 185,
                "platform_count": 4
            },
            {
                "id": "ST-02",
                "name": "Tech Hub Junction",
                "x": 440,
                "y": 280,
                "line": "Interchange (Blue/Emerald)",
                "occupancy_pct": 88,
                "status": "CRITICAL",
                "inflow_rate": 310,
                "platform_count": 6
            },
            {
                "id": "ST-03",
                "name": "Cyber Gateway",
                "x": 640,
                "y": 280,
                "line": "Interchange (Blue/Emerald)",
                "occupancy_pct": 62,
                "status": "NORMAL",
                "inflow_rate": 140,
                "platform_count": 4
            },
            {
                "id": "ST-04",
                "name": "Financial District",
                "x": 820,
                "y": 400,
                "line": "Blue Corridor",
                "occupancy_pct": 82,
                "status": "CRITICAL",
                "inflow_rate": 275,
                "platform_count": 3
            },
            {
                "id": "ST-05",
                "name": "South Port",
                "x": 120,
                "y": 480,
                "line": "Emerald Express",
                "occupancy_pct": 42,
                "status": "NORMAL",
                "inflow_rate": 95,
                "platform_count": 2
            },
            {
                "id": "ST-06",
                "name": "Market Square",
                "x": 320,
                "y": 480,
                "line": "Emerald Express",
                "occupancy_pct": 53,
                "status": "NORMAL",
                "inflow_rate": 120,
                "platform_count": 3
            },
            {
                "id": "ST-07",
                "name": "Civic Center",
                "x": 760,
                "y": 140,
                "line": "Emerald Express",
                "occupancy_pct": 47,
                "status": "NORMAL",
                "inflow_rate": 110,
                "platform_count": 2
            },
            {
                "id": "ST-08",
                "name": "Airport East Link",
                "x": 980,
                "y": 400,
                "line": "Blue Corridor",
                "occupancy_pct": 39,
                "status": "NORMAL",
                "inflow_rate": 80,
                "platform_count": 2
            }
        ]
    }