import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

NETWORK_FILE = Path(__file__).resolve().parents[2] / "data" / "nyc_network.json"


@lru_cache(maxsize=1)
def load_network() -> dict:
    """The full NYC rail network snapshot from scripts/build_network.py.

    `stations` is every station-level stop in the MTA GTFS feed (496), `segments`
    is every rail adjacency between two consecutive stops (578, deduplicated
    undirected, with the semicolon-joined route short names that use each), and
    `monitored` is the 59 station codes the dashboard tracks. The geographic map
    renders this as the base layer and overlays live congestion on `monitored`.
    """
    if not NETWORK_FILE.exists():
        logger.warning("nyc_network.json not found at %s; serving an empty network", NETWORK_FILE)
        return {"stations": [], "segments": [], "monitored": []}

    with NETWORK_FILE.open(encoding="utf-8") as fh:
        data = json.load(fh)

    codes = {s["c"] for s in data.get("stations", [])}
    dropped = 0
    segments = []
    for seg in data.get("segments", []):
        if seg["a"] in codes and seg["b"] in codes:
            segments.append(seg)
        else:
            dropped += 1
    if dropped:
        logger.warning("dropped %d network segments referencing unknown stations", dropped)

    return {
        "stations": data.get("stations", []),
        "segments": segments,
        "monitored": data.get("monitored", []),
    }