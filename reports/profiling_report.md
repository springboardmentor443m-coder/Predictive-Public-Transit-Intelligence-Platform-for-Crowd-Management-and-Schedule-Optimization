# MetroFlow — Taipei MRT Dataset Profiling Report
(mode: streaming)

## Dimensions
- Rows: 705,206,450
- Columns: 5

## Missing Values
| Column | Missing count |
| --- | --- |
| 日期 | 0 |
| 時段 | 0 |
| 進站 | 0 |
| 出站 | 0 |
| 人次 | 0 |

## Duplicates
- Duplicate rows (within-file, exact date/hour/entry/exit match): 0

## Numerical Statistics (passenger count)
### 人次
- min: 0.0
- max: 5737.0
- mean: 6.926664801491818
- std: 20.100932874002538
- n_zero: 279670165
- n_negative: 0
- note: median/percentiles omitted in streaming mode (would require full sort of 640M+ values)

## Categorical Cardinality
- Unique entry stations: 119
- Unique exit stations: 122
- Unique hour values: 24 (range [0, 23])

## Date/Time Coverage
- Date range: 2017-01-01 to 2024-01-31

## Station Coverage
- Total unique stations: 122
- Entry-only stations: 0
- Exit-only stations: 3

## Data Quality Issues
- 6139741 rows have identical entry and exit station (same-station OD pairs; may represent self-loops/placeholder rows, not errors).
- 39.7% of rows have zero passenger count — expected given the dense station OD matrix per hour, but relevant for modeling (heavy zero-inflation).