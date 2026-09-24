"""Importers for external transit ridership datasets.

Each importer parses a real-world CSV, normalizes it to the MetroFlow demo
schema via ``base``, and writes ``ridership_hourly.csv`` / ``stations.csv``
that the ``seed_db.py`` pipeline consumes.

Usage:

    python scripts/importers/cli.py --city mta  --input turnstile_240515.txt  --output-dir data
    python scripts/importers/cli.py --city seoul --input seoul_metro.csv
    python scripts/importers/cli.py --city tfl  --input tfl_entry_exit.csv
"""

from scripts.importers import base
from scripts.importers import cli
from scripts.importers import mta
from scripts.importers import seoul
from scripts.importers import tfl

__all__ = ["base", "cli", "mta", "seoul", "tfl"]