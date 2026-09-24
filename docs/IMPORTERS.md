# MetroFlow — Real-World Dataset Importers

This guide documents the production ingestion path: how genuine, agency-published CSV files
(NYC MTA, Seoul Metro, Transport for London) are parsed, normalized to the internal hourly
schema, re-anchored to *now*, and loaded through the standard seed pipeline — with zero changes
to the API, models, or dashboards.

## 1. Overview

```
agency CSV ──> scripts/importers/<city>.py   (parse real export format)
                └─> base.normalize           (aggregate → ridership_hourly.csv schema)
                      └─> re-anchor to now   (base.recenter_to_now)
                            └─> write_outputs -> data/ridership_hourly.csv + data/stations.csv
                                  └─> python scripts/seed_db.py --refresh  (→ PostgreSQL)
```

| Concept | Where | Responsibility |
|---|---|---|
| Formats | `mta.py`, `seoul.py`, `tfl.py` | Parse the genuine agency layout (cumulative counters, aliased Korean/English columns, annual totals) |
| Normalization | `base.hourly_frame()` | Aggregate per station-hour, derive `occupancy_pct`, congestion buckets, capacity |
| Day-expansion | `base.expand_day_totals_to_hourly()` / `expand_year_to_hourly()` | Spread daily/annual totals across hours using the metro demand shape |
| Re-anchoring | `base.recenter_to_now()` | Shift timestamps so the newest observation is the current hour (seed freshness rule) |
| Persistence | `base.write_outputs()` | Emit `ridership_hourly.csv` + `stations.csv` |
| CLI | `scripts/importers/cli.py` | One entrypoint for all three cities |

## 2. Quick Start

```bash
cd backend

# NYC MTA turnstile open-data file (real cumulative counters)
python scripts/importers/cli.py --city mta --input turnstile_240515.txt --output-dir data

# Seoul Metro (English or Korean columns; hourly or daily totals)
python scripts/importers/cli.py --city seoul --input seoul_metro.csv --output-dir data

# TfL Entry & Exit annual station counts
python scripts/importers/cli.py --city tfl --input tfl_entry_exit.csv --output-dir data

python scripts/seed_db.py --refresh
```

Options: `--prefix test_` writes `test_ridership_hourly.csv` (handy for validating without
clobbering `data/`); `--limit N` keeps the top-N busiest stations (default 10 → mapped to
`ST01..ST10`).

## 3. Importers Reference

### 3.1 MTA turnstile (`mta.py`)

Real format (`turnstile_*.txt` from MTA Turnstile open data):

```
C/A,UNIT,SCP,STATION,LINENAME,DIVISION,DATE,TIME,DESC,ENTRIES,EXITS
A002,R051,02-00-00,59 ST,1,IRT,05/15/2024,00:00:00,REGULAR,1234567,7654321
```

- `ENTRIES`/`EXITS` are **running counters** per audit device (`C/A`-`UNIT`-`SCP`); `DESC`
  separates `REGULAR` audits from `RECOVR_AUD`.
- The importer diffs consecutive audits (clamped ≥ 0), sums both DESC variants, and yields real
  per-station hourly traffic.
- `STATION` names are normalized to upper case; the top `--limit` stations by volume become
  `ST01..ST10`; `line` is the modal first `LINENAME` entry.

### 3.2 Seoul Metro (`seoul.py`)

Column names differ per release, so the parser resolves them by alias:

| Concept | English aliases | Korean aliases |
|---|---|---|
| Station | `station`, `station_name`… | `역명`, `역`, `지하철역` |
| Date | `date`, `year_date`… | `사용일자`, `일자`, `기준일자` |
| Hour (optional) | `hour`, `time`… | `시간`, `시각`, `시` |
| Entrants | `entries`, `board`, `in`… | `승차`, `승차승객`, `승차총승객수` |
| Exiting | `exits`, `alight`, `out`… | `하차`, `하차승객`, `하차총승객수` |

- **Hourly** source: a timestamp (or date+hour pair) is used directly.
- **Daily totals** source (no hour column): each station-day total is spread across the 24 hours
  using the metro demand shape (`expand_day_totals_to_hourly`), so the standard daily
  "승차/하차" exports still feed the hourly pipeline.
- Files are read with encoding fallbacks (`utf-8-sig` → `utf-8` → `cp949` → `cp1252`) covering
  BOM, Korean, and legacy ANSI exports.

### 3.3 TfL Entry & Exit (`tfl.py`)

The published annual station totals:

```
Year, Station, Entrances, Exits
2015, Waterloo, ..., ...
```

- Each station-year total is expanded across every day of that year and then across the 24 hours
  using the demand shape (`expand_year_to_hourly`), with weekend days softened.
- The busiest stations map to `ST01..ST10` (limit via `--limit`).

## 4. Normalization Details

### 4.1 Schema produced

Exactly the `generate_data.py` schema consumed by `seed_db.py`:

```
station_code, station_name, line, timestamp, hour, weekday,
is_weekend, is_peak, entries, exits, occupancy, capacity,
occupancy_pct, congestion_level
```

### 4.2 Occupancy & capacity

The reference `generate_data.py` uses `entries ≈ capacity × occ_pct / 4`. To preserve that
relationship (`peak-hour ⇒ ~100% occupancy`) for unlabeled real data:

- `capacity` is inferred per station as the 99th-percentile hourly flow × 4, clamped to
  `[400, 20 000]` (`base.default_capacity`).
- `occupancy_pct = clamp(4 × entries / capacity, 2%, 115%)`.
- `occupancy = round(entries)`.

### 4.3 Re-anchoring

`seed_db.py` only trusts `ridership_hourly.csv` when its newest row is ≤ 3 days old; otherwise it
synthesizes a now-anchored window. `base.recenter_to_now()` shifts every timestamp (preserving
hour alignment and weekday) so the newest observation is the current hour — imported data is
therefore always "fresh" and appears on the live dashboards. Re-anchoring runs **before**
aggregation so the derived `hour`/`weekday` columns stay consistent with the exported timestamps.

### 4.4 Seed integration

`seed_db.py` reads the produced files verbatim:

- `stations.csv` → creates `Station` rows (imported names/lines/capacities); the scheduler's line
  grouping uses `line`. If an imported line has no matching seeded `TR-*` fleet (e.g. MTA line
  `4`), the seeder falls back to any active train so the timetable, live train map and traffic
  series still populate.
- `ridership_hourly.csv` → the newest 7-day window becomes `RidershipRecord` history.

## 5. Verified End-to-End

Each importer was validated against a realistic sample in the genuine export format:

| City | Sample | Result |
|---|---|---|
| mta | 4 stations × 3 days of cumulative counters | 284 station-hours; stations `ST01..ST04` with modal line names |
| seoul | Korean daily totals, 3 stations × 4 days | 288 station-hours; names decoded (강남역 / 역삼역 / 삼성역) |
| tfl | 5 stations × 1 year | 4 stations × ~8.7k hours after `--limit 4` |

`cli.py` → `seed_db.py --refresh` produced **20,736 schedules + 284 ridership rows** from the
imported MTA file, confirming the full path.

## 6. Adding a New City

1. Create `scripts/importers/<city>.py` exposing `parse(path, limit=10)` returning
   `(detail, name_by_code, line_by_code)` where `detail` has columns
   `station_code, timestamp, entries, exits` (station codes ranked `ST01..ST10`); or emit a
   daily/annual frame and call `base.expand_day_totals_to_hourly()` /
   `base.expand_year_to_hourly()` first.
2. Register it in `IMPORTERS = {...}` in `cli.py`.
3. Write a sample in the genuine format and run
   `cli.py --city <city> --input sample.csv --prefix test_` to verify the schema.
4. Document the aliases in this file's reference table.

## 7. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Unrecognized MTA turnstile format: missing columns ...` | File is not the turnstile cumulative-counter layout (e.g. the compact `.tsv`); provide the weekly `turnstile_*.txt` |
| `Could not find a {station/entries/...} column ...` | Column aliases don't match; check the file header and extend the alias list, or pre-normalize the columns |
| Mojibake station names | File encoding not covered; re-save as UTF-8 (BOM) or `cp949`, or extend the `read_csv` fallback chain |
| Re-anchoring makes dates the same but times strange | Re-centering shifts wall-clock time; hour alignment is preserved so patterns (peak morning/evening) stay correct |
| `db` tables unaffected | Importers only write CSV files; run `python scripts/seed_db.py --refresh` afterwards |