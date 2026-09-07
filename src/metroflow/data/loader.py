"""Read-only loading utilities for the raw Taipei MRT hourly OD dataset.

These functions never write to, delete, or otherwise modify files under
RAW_DATA_DIR. They only read the raw parquet files into memory.
"""
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.settings import RAW_DATA_DIR, RAW_DATA_GLOB, RAW_COLUMNS


def discover_raw_files(raw_data_dir: Path = RAW_DATA_DIR, pattern: str = RAW_DATA_GLOB) -> list[Path]:
    """Return the sorted list of raw monthly parquet files found on disk."""
    matches = sorted(glob.glob(str(raw_data_dir / pattern)))
    if not matches:
        raise FileNotFoundError(
            f"No raw dataset files matching '{pattern}' found under {raw_data_dir}"
        )
    return [Path(m) for m in matches]


def load_single_file(file_path: Path) -> pd.DataFrame:
    """Load one monthly parquet file without mutating it on disk."""
    df = pd.read_parquet(file_path)
    missing = set(RAW_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{file_path.name} is missing expected columns: {missing}")
    return df


def load_raw_dataset(
    raw_data_dir: Path = RAW_DATA_DIR,
    pattern: str = RAW_DATA_GLOB,
    file_limit: int | None = None,
) -> pd.DataFrame:
    """Load and concatenate all raw monthly files into a single DataFrame.

    Parameters
    ----------
    file_limit:
        Optional cap on the number of monthly files to load, useful for
        quick local iteration. ``None`` loads the full dataset.
    """
    files = discover_raw_files(raw_data_dir, pattern)
    if file_limit is not None:
        files = files[:file_limit]

    frames: list[pd.DataFrame] = []
    for file_path in files:
        df = load_single_file(file_path)
        df["source_file"] = file_path.name
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    return combined


def raw_file_manifest(raw_data_dir: Path = RAW_DATA_DIR, pattern: str = RAW_DATA_GLOB) -> list[dict]:
    """Return per-file metadata (name, size) without loading full contents."""
    files = discover_raw_files(raw_data_dir, pattern)
    return [
        {"file_name": f.name, "size_bytes": os.path.getsize(f)}
        for f in files
    ]
