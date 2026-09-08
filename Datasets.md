# AI MetroFlow: KAGGLE-ONLY Dataset Resources (PRE-2021 Verified)

**Project:** "AI Predictive Public Transit Intelligence Platform for Crowd Management and Schedule Optimization"

---

**Total Datasets: 7** (all verified pre-2021, real observational data, working Kaggle links.
Excludes Ridership / Ticketing / Smart Card datasets per request.)

---

## Crowd Monitoring / Passenger Density / Station Footfall

### 1. Seoul Metro Usage (Subway Entry/Exit Records)

- **Module:** Crowd Monitoring, Station Footfall, Inflow/Outflow analysis
- **Description:** Station-wise hourly boarding (`people_in`) and alighting (`people_out`) for Seoul Metro Lines 1-8, 2015-2021. Cleaned UTF-8 CSVs with station metadata file (`seoul-metro-station-info.csv`). Directly enables peak-hour, inflow/outflow and congestion analysis.
- **Year:** 2015-2021 (pre-2021)
- **Link:** https://www.kaggle.com/datasets/kimjmin/seoul-metro-usage
- **Format:** CSV

### 2. NYC Subway Traffic 2017-2021 (Hourly Station Traffic)

- **Module:** Crowd Monitoring, Congestion forecasting, Time-series modeling
- **Description:** 4-hour interval entry/exit counts for 469 NYC subway stations (Feb 2017 - Aug 2021), plus neighborhood census data. Ideal for passenger density estimation and concept-drift / peak-hour analysis in the pre-2021 (pre/post-COVID lockdown) era.
- **Year:** Feb 2017 - Aug 2021 (pre-2021)
- **Link:** https://www.kaggle.com/datasets/eddeng/nyc-subway-traffic-data-20172021
- **Format:** CSV

### 3. Transport for London (TfL) Entry & Exit Dataset

- **Module:** Crowd Monitoring, Station footfall, Demand trends
- **Description:** Yearly entry/exit totals (2007-2021) for 435 London stations, 8 lines, network type (Underground/Night Tube), with geodata and Tube maps.
- **Year:** 2007-2021 (pre-2021)
- **Link:** https://www.kaggle.com/datasets/olisao/transport-for-london-tfl-entry-and-exit-dataset
- **Format:** CSV

### 4. Beijing Metro Passengers (Card-Swiping O-D Records, Jan 2019)

- **Module:** Crowd Monitoring, Origin-Destination flow, Congestion modeling
- **Description:** Real card-swiping transaction records of Beijing metro passengers (Jan 2019). Fields: entry/exit line & station, `entry_tm`, `exit_tm`. Enables station- and line-level passenger flow, OD analysis, and time-of-day congestion estimation.
- **Year:** Jan 2019
- **Link:** https://www.kaggle.com/datasets/itsncut/data-of-metro-passengers-in-beijing
- **Format:** CSV

## AI Prediction / Passenger Flow Forecasting

### 5. Hangzhou Metro Traffic Prediction (Large-Scale Passenger Flow)

- **Module:** AI Prediction, Passenger flow forecasting, Network modeling
- **Description:** Large-scale metro traffic prediction dataset (card-swiping records from 81 stations / 3 lines, Jan 2019) with train/test splits and a road map CSV (network topology). Builds station-graph models for passenger flow prediction. (4.26 GB)
- **Year:** Jan 2019
- **Link:** https://www.kaggle.com/datasets/zjplab/hangzhou-metro-traffic-prediction
- **Format:** CSV

## Metro Scheduling / Delays (Occupancy Approximated from Passenger-Flow Sets)

> **NOTE:** No pre-2021 metro-specific occupancy dataset is verifiably available on Kaggle.
> Occupancy / crowding is instead approximated from the station and line passenger-flow
> datasets (#1 Seoul, #4 Beijing, #5 Hangzhou). Scheduling and Delays are covered below.

### 6. Railway Delay Dataset (2015, Stop-Level)

- **Module:** Scheduling, Delay prediction, AI prediction
- **Description:** 312,040 rail journey records (year 2015) for delay prediction. Features: distance, weather, day of week, time of day, train type, historical delay, and route congestion. Directly trains delay-impact prediction models. NOTE: sampled rows carry US carrier codes but the schema is delay-prediction ready.
- **Year:** 2015
- **Link:** https://www.kaggle.com/datasets/anuragraturi/railway-delay-dataset
- **Format:** CSV

### 7. NJ Transit + Amtrak (NEC) Rail Performance

- **Module:** Scheduling, Delay handling, Schedule vs actual analysis
- **Description:** Stop-level, minute-resolution records for ~287,000+ train trips (NJ Transit + Amtrak Northeast Corridor), covering Mar 2018 - Apr 2019. Columns: scheduled vs actual times, `delay_minutes`, station. Ideal for schedule-optimization and delay-notification modules.
- **Year:** Mar 2018 - Apr 2019 (pre-2021)
- **Link:** https://www.kaggle.com/datasets/pranavbadami/nj-transit-amtrak-nec-performance
- **Format:** CSV

---

## Quick Reference

### Crowd Monitoring / Passenger Density

1. Seoul Metro Usage (2015-2021) — https://www.kaggle.com/datasets/kimjmin/seoul-metro-usage
2. NYC Subway Traffic 2017-2021 — https://www.kaggle.com/datasets/eddeng/nyc-subway-traffic-data-20172021
3. TfL Entry & Exit (2007-2021) — https://www.kaggle.com/datasets/olisao/transport-for-london-tfl-entry-and-exit-dataset
4. Beijing Metro Passengers (Jan 2019) — https://www.kaggle.com/datasets/itsncut/data-of-metro-passengers-in-beijing

### AI Prediction / Passenger Flow

5. Hangzhou Metro Traffic Prediction (Jan 2019) — https://www.kaggle.com/datasets/zjplab/hangzhou-metro-traffic-prediction

### Metro Scheduling / Delays

6. Railway Delay Dataset (2015) — https://www.kaggle.com/datasets/anuragraturi/railway-delay-dataset
7. NJ Transit + Amtrak NEC Performance (2018-2019) — https://www.kaggle.com/datasets/pranavbadami/nj-transit-amtrak-nec-performance
