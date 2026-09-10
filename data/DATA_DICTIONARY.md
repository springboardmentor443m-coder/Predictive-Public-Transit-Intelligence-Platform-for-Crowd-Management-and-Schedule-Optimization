# Data Dictionary

| Column | Meaning |
|---|---|
| timestamp | Observation timestamp (timezone-aware in source file) |
| station_code | Station identifier |
| people_in | Passenger entries |
| people_out | Passenger exits |

Derived in the application:
- total_flow = people_in + people_out
- hour
- day_of_week
- month
- dayofyear
- line (inferred from the leading digit of station code for Lines 1–8)
