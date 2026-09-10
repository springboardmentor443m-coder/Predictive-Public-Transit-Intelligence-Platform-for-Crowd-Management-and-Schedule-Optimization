# Database Schema / Data Model

The prototype uses the CSV as the source-of-truth dataset. The logical relational design for a future PostgreSQL implementation is:

## passenger_flow
| Field | Type | Description |
|---|---|---|
| timestamp | TIMESTAMP | Observation time |
| station_code | INTEGER | Seoul station code |
| people_in | INTEGER | Passenger entries |
| people_out | INTEGER | Passenger exits |
| total_flow | INTEGER | Derived entries + exits |

## station
| Field | Type | Description |
|---|---|---|
| station_code | INTEGER | Primary key / source station identifier |
| station_name | TEXT | To be populated from official station metadata |
| line | TEXT | Metro line |

## schedule_recommendation
| Field | Type | Description |
|---|---|---|
| station_code | INTEGER | Station |
| planning_hour | INTEGER | Hour |
| predicted_demand | FLOAT | Model prediction |
| recommended_headway_min | INTEGER | Planning recommendation |
| trains_per_hour | FLOAT | Derived frequency |

No real timetable values are stored in the supplied passenger log, so official timetable data should be connected as a separate source before claiming exact arrival/departure times.
