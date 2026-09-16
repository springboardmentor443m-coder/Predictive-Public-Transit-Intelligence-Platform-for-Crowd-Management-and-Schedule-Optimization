# MetroFlow

An AI-powered platform that predicts NYC subway station crowd levels
and recommends schedule adjustments, built as the internship project
for "Predictive Public Transit Intelligence Platform for Crowd
Management and Schedule Optimization."

## What this actually is

A decision-support tool, not a live camera/sensor system. It learns
patterns from real historical ridership data (station, time of day, day
of week, holidays) and predicts how crowded a station will be, then
turns that prediction into a scheduling recommendation and alerts. No
computer vision or CCTV is used, matching the brief's explicit scope.

## How it maps to the official brief

| Brief module | This project |
|---|---|
| User Management | Two-role login (admin / operator) with a profile indicator in the sidebar - lightweight, not full JWT/RBAC |
| Crowd Monitoring | Trained prediction model + interactive crowd-level map + station table |
| Scheduling Management | `scheduling.py` - capacity-based recommendation logic, plus simulated train headway |
| AI Prediction | RandomForestRegressor predicting passenger count per station/hour, evaluated honestly on real data |
| Alert & Notification | TWO separate alert types (overcrowding + delay), plus an admin-only emergency broadcast banner |
| Analytics Dashboard | Summary stats, traffic pattern charts (by hour/day), and a downloadable per-station performance report |
| Extra: NL query | `/query` endpoint - ask a plain-English question, get an answer generated from a real model prediction |

## Data

**Real data** from the MTA Subway Hourly Ridership 2022-2024 dataset
(NY State official open data portal / Kaggle). The original file is
~51 million rows across hundreds of stations. It was processed down to
a workable, well-scoped dataset, in a Kaggle notebook:

1. Combined the OMNY/MetroCard payment-method split into one ridership
   total per station/timestamp (`groupby` + `sum`): 51M -> 7.68M rows.
2. Filtered to the 12 busiest stations by total ridership (Times Sq-42
   St, Grand Central-42 St, Union Sq, Herald Sq, Penn Station, and
   others) - a reasonable scope for the timeline, mirroring how a real
   transit authority would prioritize its busiest hubs: 7.68M -> 300,242 rows.
3. Engineered `hour`, `day_of_week`, `is_weekend`, and `is_holiday`
   (2023 US federal holidays) features from the raw timestamp.

**Base file:** `data/metroflow_final.csv` - 300,242 rows, 9 columns,
zero nulls, a full year of real data across all 12 stations.

**Enriched file:** `data/metroflow_enriched.csv` - the same data plus
capacity, crowd_pct, crowd_level, and the three simulated columns
below (15 columns total). Built and verified directly in the project's
Kaggle notebook, matching the backend's live calculations exactly.

## Station capacity & crowd levels (a bug was caught and fixed here)

MTA doesn't publish official per-station capacity figures, so each
station's capacity is estimated as **1.1x its own historical peak
passenger_count** - not one shared number across all 12 stations.

An earlier version of this used a 1.3x multiplier, which turned out to
be a real bug: with that much buffer, no row could mathematically ever
reach the "high" crowd band, since even a station's single busiest
hour ever recorded would fall under 80% of a 1.3x-padded capacity.
This was caught, explained, and fixed to 1.1x, then verified against
the real dataset: **290,187 low / 9,443 medium / 612 high** crowd-level
station-hours, with a maximum crowd_pct of 90.9% - a realistic,
non-inflated distribution.

Bands: <50% of capacity = low, 50-80% = medium, 80%+ = high.

## AI Prediction Model

`RandomForestRegressor` (scikit-learn) predicting `passenger_count`
from hour, is_weekend, is_holiday, station, day_of_week, and a
time-of-day bucket (morning_peak / evening_peak / midday / off_peak),
all label-encoded. Trained and evaluated on the real dataset:

- **MAE: ~720 passengers**
- **R²: ~0.64**
- **~54% improvement over a naive mean-baseline**

This is reported honestly as a legitimate real-world result, not
inflated. Real ridership data is noisier than synthetic data would be,
and a model explaining 64% of real-world variation using only
time/station features is a meaningful, defensible result - not a
shortfall to hide.

## Simulated operational layers (clearly labeled, not real)

No public dataset provides these at station-level granularity for NYC
subway, so each is a documented, rule-based simulation - not presented
as real sensor/GPS data:

- **Train arrival/departure timing**: simulated headway - 3.5 min at
  peak hours (8-10, 17-19), 6 min midday, 9 min off-peak.
- **Entry vs. exit split**: the real dataset only contains entries
  (turnstile swipe-ins). Simulated exits = average entries from ~1
  hour earlier at that station (a rough proxy for typical trip
  duration).
- **Delay**: increases as a station's crowd % exceeds its "high"
  threshold, plus small random noise - derived FROM the real
  prediction, not a disconnected random number.

## Project structure

```
metroflow/
├── data/
│   ├── metroflow_final.csv       # base real dataset (300,242 rows, 9 cols)
│   └── metroflow_enriched.csv    # + capacity, crowd %/level, simulated layers (15 cols)
├── model/
│   ├── train_model_real.py       # feature engineering + model training on real data
│   ├── scheduling.py             # capacity table, crowd %, alerts, simulated layers
│   └── metroflow_model.joblib    # trained model + encoders (generated by train_model_real.py)
├── backend/
│   └── main.py                   # FastAPI backend - all endpoints
├── dashboard/
│   └── app.py                    # Streamlit frontend - login, map, alerts, charts, NL query
├── requirements.txt
└── README.md
```

## How to run it

Requires Python 3.9+. From the project root:

```bash
pip install -r requirements.txt

# Dataset and trained model are already included.
# To retrain from scratch: cd model && python train_model_real.py && cd ..

# Start the backend (leave running in its own terminal)
cd backend && uvicorn main:app --reload --port 8000

# In a NEW terminal, start the dashboard
cd dashboard && streamlit run app.py
```

Open the Streamlit URL it prints (usually `http://localhost:8501`).

**Demo credentials:**
- `admin` / `admin123` - full access, including emergency broadcast
- `operator` / `operator123` - view-only monitoring

(Change these before sharing the app with anyone else.)

## Dashboard features

- Two-role login with a sidebar profile indicator
- Admin-only emergency broadcast banner
- Two separate alert types: overcrowding alert and delay alert
- Interactive crowd-level map (color-coded, sized by predicted volume)
- Per-station recommendations table
- Traffic pattern charts: average ridership by hour of day and by day
  of week
- Downloadable per-station performance report (capacity, peak hour,
  average crowd %, % of hours spent in "high" crowd)
- Natural-language query box: ask a plain-English question, get an
  answer generated from a real model prediction

## Natural-language query feature

The `/query` endpoint uses simple pattern matching (regex) to pull a
station name and time out of your question, gets a REAL prediction
from the trained model, and phrases the answer in plain English. The
numbers always come from the model - this keeps the feature honest
rather than letting an LLM invent figures.

**To upgrade this to a full LLM-powered version** (optional future
enhancement): in `backend/main.py`'s `/query` endpoint, send the
prediction as context to an LLM API and ask it to phrase a more
natural, conversational answer - the LLM explains the number, it
doesn't generate it.

## Limitations & what real deployment would add

- Station capacity, train arrival/departure timing, entry/exit split,
  and delay are simulated with documented, defensible rules - not
  sourced from real sensors or GPS feeds, since no such public dataset
  exists at this granularity for NYC subway.
- Scheduling recommendations are threshold-based rules, not a full
  optimization solver (e.g. linear programming for vehicle allocation)
  - a reasonable, documented scope choice for this timeline.
- No real-time data pipeline; predictions are computed on-demand from
  historical patterns, not live sensor feeds.
- Login uses two hardcoded demo accounts, not a real user database
  with full role-based permissions.
- Future enhancement: integrate live MTA GTFS-realtime feeds for real
  train position/delay data, and a real entry/exit dataset if one
  becomes available, to replace the simulated layers with real ones.