# MetroFlow Data — NYC Subway Traffic 2017–21 (chosen dataset)
Source: https://www.kaggle.com/datasets/eddeng/nyc-subway-traffic-data-20172021
Hourly entry/exit for 469 stations.

## Why NYC over Seoul Metro Usage?
| Criterion | NYC Subway Traffic 2017-21 | Seoul Metro Usage 2015-21 |
|---|---|---|
| Granularity | Hourly entries AND exits per station | Hourly boardings/alightings (coarser) |
| Stations | 469 | ~300 |
| Inflow/outflow split | Yes (needed for net-flow + density) | Partial |
| Peak-hour modeling | Direct (AM/PM bimodal clearly visible) | Good but Korean station names complicate demo |
| Scheduling use | Demand -> headway mapping per station-hour | Same but less exit data |
| Language/docs | English, MTA open-data compatible | Mixed KR/EN |

Chosen: **NYC Subway Traffic 2017–21** for crowd monitoring, congestion levels,
inflow/outflow analysis, peak-hour forecasting, and frequency optimization.

## Use real data (optional)
```bash
pip install kagglehub
python -c "import kagglehub; kagglehub.dataset_download('eddeng/nyc-subway-traffic-data-20172021')"
# Then place the CSV in data/ and update backend .env DATA_PATH, or rename columns to:
# station_code, timestamp, entries, exits
# The loader in backend/app/ml/data_loader.py auto-normalizes common variants.
```

## Bundled sample (default, no auth needed)
```bash
pip install pandas numpy
python data/generate_sample.py --stations 12 --days 90
# -> data/nyc_subway_sample.csv  (~25k rows, 12 stations, bimodal peaks + weekend effect)
```
Backend seed + training read this file automatically.
