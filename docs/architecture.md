# System Architecture

```text
                 ┌──────────────────────────────┐
                 │       MetroFlow Web UI       │
                 │          Streamlit           │
                 └──────────────┬───────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
       Crowd Monitor       AI Forecast       Schedule Planner
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                       Data Processing Layer
                                │
                 Seoul Metro passenger logs
                                │
                    Random Forest ML Model
                                │
                  Reports / Recommendations
```

## Roles
- **Admin:** full dashboard and operational views.
- **Operator:** monitoring, forecasting and schedule-planning views.

## Data flow
1. Load the supplied Seoul Metro passenger log.
2. Parse timestamps and derive hour/day/month features.
3. Calculate passenger flow = entries + exits.
4. Aggregate data for monitoring.
5. Use the trained Random Forest model for demand prediction.
6. Convert predicted demand into a transparent headway recommendation.
