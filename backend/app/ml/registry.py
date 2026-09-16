import os

SUPPORTED_CITIES = ("seoul", "hangzhou", "nyc", "tfl", "beijing")
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
    # NYC Subway Traffic 2017-2021 (469 stations, 4h intervals) — maps to
    # representative complex/station ids; full 469-station artifacts trainable
    # via kaggle/04_nyc_crowd_demand.py.
    "nyc": {
        "ST01": "127", "ST02": "128", "ST03": "129", "ST04": "130", "ST05": "131",
        "ST06": "132", "ST07": "133", "ST08": "134", "ST09": "135", "ST10": "136",
    },
    # TfL Entry & Exit (435 stations, yearly 2007-2021) — maps to top
    # footfall stations; see kaggle/05_tfl_crowd_demand.py.
    "tfl": {
        "ST01": "940GZZLUKSX", "ST02": "940GZZLUVIC", "ST03": "940GZZLUWLO",
        "ST04": "940GZZLULNB", "ST05": "940GZZLUEUS", "ST06": "940GZZLUCHX",
        "ST07": "940GZZLUBNK", "ST08": "940GZZLUPAC", "ST09": "940GZZLUOXF",
        "ST10": "940GZZLUTMY",
    },
    # Beijing Metro O-D (Jan 2019 card swipes) — maps to line/station codes;
    # see kaggle/06_beijing_crowd_demand.py.
    "beijing": {
        "ST01": "BJ01", "ST02": "BJ02", "ST03": "BJ03", "ST04": "BJ04", "ST05": "BJ05",
        "ST06": "BJ06", "ST07": "BJ07", "ST08": "BJ08", "ST09": "BJ09", "ST10": "BJ10",
    },
}


def model_city() -> str:
    city = os.environ.get("METROFLOW_MODEL_CITY", DEFAULT_CITY).lower()
    return city if city in SUPPORTED_CITIES else DEFAULT_CITY


def city_station_code(station_id: str | None) -> str | None:
    if not station_id:
        return None
    return CITY_STATION_MAP.get(model_city(), {}).get(station_id)