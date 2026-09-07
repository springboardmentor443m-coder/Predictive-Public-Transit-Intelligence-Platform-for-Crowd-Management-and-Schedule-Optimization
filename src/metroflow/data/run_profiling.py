"""Step 1 entry point: Data Ingestion and Data Profiling.

Usage
-----
    python -m metroflow.data.run_profiling [--file-limit N]

Loads the raw Taipei MRT hourly OD dataset (read-only), validates it,
computes profiling statistics, and writes JSON + Markdown reports under
``reports/``.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from metroflow.data.loader import discover_raw_files, load_raw_dataset, raw_file_manifest
from metroflow.data.profiler import build_profile_report
from metroflow.data.streaming_profiler import run_streaming_profile
from metroflow.data.report_writer import write_json_report, write_markdown_report
from config.settings import PROFILE_REPORT_JSON_PATH, PROFILE_REPORT_MD_PATH, RAW_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("metroflow.profiling")


def main(file_limit: int | None, mode: str) -> None:
    logger.info("Discovering raw dataset files under %s", RAW_DATA_DIR)
    manifest = raw_file_manifest()
    logger.info("Found %d raw monthly files", len(manifest))

    if mode == "streaming":
        logger.info("Running streaming (memory-safe, file-by-file) profiling...")
        report = run_streaming_profile(file_limit=file_limit)
    else:
        logger.info("Loading raw dataset into memory (file_limit=%s)...", file_limit)
        df = load_raw_dataset(file_limit=file_limit)
        logger.info("Loaded dataframe with shape %s", df.shape)
        logger.info("Building profiling report...")
        report = build_profile_report(df)

    report["source_manifest"] = {
        "mode": mode,
        "n_files_loaded": len(discover_raw_files()) if file_limit is None else file_limit,
        "n_files_available": len(manifest),
        "file_names": [m["file_name"] for m in manifest],
    }

    write_json_report(report)
    write_markdown_report(report)
    logger.info("Wrote profiling reports to %s and %s", PROFILE_REPORT_JSON_PATH, PROFILE_REPORT_MD_PATH)

    logger.info("Data quality issues found: %d", len(report["data_quality_issues"]))
    for issue in report["data_quality_issues"]:
        logger.info(" - %s", issue)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MetroFlow Step 1: Data Ingestion & Profiling")
    parser.add_argument(
        "--file-limit",
        type=int,
        default=None,
        help="Optional cap on number of monthly files to load (for quick iteration).",
    )
    parser.add_argument(
        "--mode",
        choices=["streaming", "in_memory"],
        default="streaming",
        help="'streaming' processes one monthly file at a time (memory-safe, default). "
        "'in_memory' loads all files into a single DataFrame (fine for small --file-limit only).",
    )
    args = parser.parse_args()
    main(args.file_limit, args.mode)
