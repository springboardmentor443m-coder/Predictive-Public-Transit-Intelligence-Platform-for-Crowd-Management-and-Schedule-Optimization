import os

SUPPORTED_CITIES = ("seoul", "hangzhou", "nyc", "tfl", "beijing")
DEFAULT_CITY = "nyc"

# Legacy translation tables for the external Kaggle corpora. The app itself runs
# on real MTA stop ids (see data/stations.csv), so "nyc" needs no translation --
# `city_station_code` passes native ids straight through.
CITY_STATION_MAP = {
    "seoul": {
        "ST01": "222", "ST02": "216", "ST03": "239", "ST04": "230", "ST05": "232",
        "ST06": "234", "ST07": "329", "ST08": "219", "ST09": "220", "ST10": "150",
    },
    "hangzhou": {
        "ST01": "015", "ST02": "009", "ST03": "004", "ST04": "007", "ST05": "010",
        "ST06": "011", "ST07": "020", "ST08": "012", "ST09": "008", "ST10": "033",
    },
    # NYC Subway Traffic 2017-2021 (469 stations, 4h intervals) — the app is
    # already keyed by MTA stop id, so this map is intentionally empty.
    "nyc": {},
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
    city = model_city()
    mapping = CITY_STATION_MAP.get(city, {})
    if station_id in mapping:
        return mapping[station_id]
    # The NYC model is trained on this app's own ridership, whose station keys
    # are already MTA stop ids, so no translation applies.
    if city == "nyc":
        return station_id
    return None