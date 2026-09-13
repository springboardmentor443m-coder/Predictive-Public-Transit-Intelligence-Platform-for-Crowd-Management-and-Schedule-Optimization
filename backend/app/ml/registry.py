import os

SUPPORTED_CITIES = ("seoul", "hangzhou")
DEFAULT_CITY = "hangzhou"

CITY_STATION_MAP = {
    "seoul": {
        "ST01": "222", "ST02": "216", "ST03": "239", "ST04": "230", "ST05": "232",
        "ST06": "234", "ST07": "329", "ST08": "219", "ST09": "220", "ST10": "150",
    },
    "hangzhou": {
        "ST01": "015", "ST02": "009", "ST03": "004", "ST04": "007", "ST05": "010",
        "ST06": "011", "ST07": "020", "ST08": "012", "ST09": "008", "ST10": "033",
    },
}


def model_city() -> str:
    city = os.environ.get("METROFLOW_MODEL_CITY", DEFAULT_CITY).lower()
    return city if city in SUPPORTED_CITIES else DEFAULT_CITY


def city_station_code(station_id: str | None) -> str | None:
    if not station_id:
        return None
    return CITY_STATION_MAP.get(model_city(), {}).get(station_id)