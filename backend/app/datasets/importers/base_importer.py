from abc import ABC, abstractmethod
import pandas as pd


class BaseTransitImporter(ABC):
    """Abstract Base Class for external dataset importers."""

    @abstractmethod
    def parse_and_normalize(self, filepath: str) -> pd.DataFrame:
        """
        Reads raw file and normalizes into standard MetroFlow schema:
        Columns: [timestamp, station_id, station_code, station_name, line_name, hour, minute,
                  day_of_week, is_weekend, capacity, inflow_ppm, outflow_ppm, line_delay_min, density_pct]
        """
        pass
