"""Render a profiling report dict to JSON and Markdown files."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.settings import PROFILE_REPORT_JSON_PATH, PROFILE_REPORT_MD_PATH, REPORTS_DIR


def write_json_report(report: dict[str, Any], path: Path = PROFILE_REPORT_JSON_PATH) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def write_markdown_report(report: dict[str, Any], path: Path = PROFILE_REPORT_MD_PATH) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    mode = report.get("source_manifest", {}).get("mode", "in_memory")
    lines: list[str] = ["# MetroFlow — Taipei MRT Dataset Profiling Report", f"(mode: {mode})", ""]

    dims = report["dimensions"]
    lines += [
        "## Dimensions",
        f"- Rows: {dims['n_rows']:,}",
        f"- Columns: {dims['n_columns']}",
        "",
    ]

    if "columns" in report:
        lines += ["## Columns", "| Column | Dtype | Unique values |", "| --- | --- | --- |"]
        for col, info in report["columns"].items():
            lines.append(f"| {col} | {info['dtype']} | {info['n_unique']:,} |")
        lines.append("")

    lines += ["## Missing Values"]
    missing = report["missing_values"]
    if isinstance(next(iter(missing.values()), 0), dict):
        lines += ["| Column | Missing count | Missing % |", "| --- | --- | --- |"]
        for col, info in missing.items():
            lines.append(f"| {col} | {info['missing_count']:,} | {info['missing_pct']}% |")
    else:
        lines += ["| Column | Missing count |", "| --- | --- |"]
        for col, count in missing.items():
            lines.append(f"| {col} | {count:,} |")

    dup = report["duplicates"]
    if "n_duplicate_rows" in dup:
        lines += ["", "## Duplicates", f"- Duplicate rows: {dup['n_duplicate_rows']:,} ({dup['duplicate_pct']}%)"]
    else:
        lines += [
            "",
            "## Duplicates",
            f"- Duplicate rows (within-file, exact date/hour/entry/exit match): {dup['n_duplicate_rows_within_file']:,}",
        ]

    lines += ["", "## Numerical Statistics (passenger count)"]
    for col, stats in report["numerical_statistics"].items():
        lines.append(f"### {col}")
        for k, v in stats.items():
            lines.append(f"- {k}: {v}")

    cc = report["categorical_cardinality"]
    lines += [
        "",
        "## Categorical Cardinality",
        f"- Unique entry stations: {cc['n_unique_entry_stations']}",
        f"- Unique exit stations: {cc['n_unique_exit_stations']}",
        f"- Unique hour values: {cc['n_unique_hour_values']} (range {cc['hour_value_range']})",
    ]

    dt = report["datetime_coverage"]
    lines += ["", "## Date/Time Coverage", f"- Date range: {dt['min_date']} to {dt['max_date']}"]
    if "n_calendar_days_in_range" in dt:
        lines += [
            f"- Calendar days in range: {dt['n_calendar_days_in_range']:,}",
            f"- Days observed: {dt['n_days_observed']:,}",
            f"- Days missing: {dt['n_days_missing']:,}",
            f"- Unparseable dates: {dt['n_unparseable_dates']}",
        ]

    sc = report["station_coverage"]
    lines += [
        "",
        "## Station Coverage",
        f"- Total unique stations: {sc['n_total_unique_stations']}",
        f"- Entry-only stations: {sc['n_entry_only_stations']}",
        f"- Exit-only stations: {sc['n_exit_only_stations']}",
    ]

    lines += ["", "## Data Quality Issues"]
    issues = report["data_quality_issues"]
    if issues:
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("- None detected.")

    path.write_text("\n".join(lines), encoding="utf-8")
