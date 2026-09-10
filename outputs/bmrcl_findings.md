# BMRCL Ridership Analysis - Findings

## Dataset Overview

- Dataset contains 92,280 records.
- Dataset contains 4 columns:
  - Date
  - Hour
  - Station
  - Ridership
- There are 83 unique stations.
- There are 48 unique dates.
- Hour values range from 0 to 23.
- No missing values were found.
- No duplicate rows were found.

## Hourly Ridership Findings

The analysis shows clear variation in ridership throughout the day.

The highest total ridership occurs at Hour 18 (6 PM), with approximately 3.33 million passengers across all stations and dates.

The top 5 hours by average ridership per record are:

1. Hour 18 - approximately 866 passengers per record
2. Hour 9 - approximately 808 passengers per record
3. Hour 17 - approximately 746 passengers per record
4. Hour 19 - approximately 713 passengers per record
5. Hour 8 - approximately 685 passengers per record

The lowest ridership occurs during the early morning hours. Hour 1 has zero recorded ridership.

These patterns indicate that passenger demand is particularly high during morning and evening commuting periods.

## Station-wise Findings

The stations with the highest total ridership include:

1. Nadaprabhu Kempegowda Station, Majestic - 1,649,530
2. Benniganahalli - 1,250,656
3. Indiranagar - 1,048,936
4. Mahatma Gandhi Road - 1,007,176
5. Krishnarajapura - 904,508
6. Mantri Square Sampige Road - 796,520
7. Chickpete - 737,856
8. Cubbon Park - 666,237
9. Yeshwantpur - 666,189
10. Baiyappanahalli - 644,624

The analysis also identified stations with comparatively lower total ridership, including Beretana Agrahara, Singasandra, Manjunathnagara, Biocon Hebbagodi and Huskur Road.

This station-level variation can help identify locations that may require greater crowd monitoring and operational attention.

## Daily Ridership Findings

Daily ridership was calculated by grouping passenger records by date.

- Highest ridership day: 2025-08-14
- Ridership on highest day: 843,684 passengers
- Lowest ridership day: 2025-08-10
- Ridership on lowest day: 482,205 passengers

The difference between the highest and lowest ridership days shows that passenger demand varies significantly from day to day.

Daily ridership trends can be used as a starting point for future passenger demand forecasting.

## Peak and Off-Peak Analysis

The dataset was divided into operational time periods:

- Morning Peak: 07:00-10:00
- Midday: 11:00-16:00
- Evening Peak: 17:00-20:00
- Off-Peak: remaining hours

The average ridership by period was:

- Evening Peak: approximately 700 passengers per record
- Morning Peak: approximately 614 passengers per record
- Midday: approximately 475 passengers per record
- Off-Peak: approximately 70 passengers per record

The Evening Peak has the highest average ridership.

This indicates that evening hours are an important period for crowd monitoring and potential train-frequency optimization.

## Weekday vs Weekend Findings

Ridership was also analyzed according to the day of the week.

The average ridership for each day was:

- Monday: approximately 392 passengers per record
- Tuesday: approximately 390 passengers per record
- Wednesday: approximately 402 passengers per record
- Thursday: approximately 402 passengers per record
- Friday: approximately 368 passengers per record
- Saturday: approximately 345 passengers per record
- Sunday: approximately 271 passengers per record

Thursday has the highest average ridership at approximately 402 passengers per record.

Sunday has the lowest average ridership at approximately 271 passengers per record.

The weekday vs weekend comparison shows:

- Weekday average ridership: approximately 390 passengers per record
- Weekend average ridership: approximately 308 passengers per record

Overall, weekday ridership is higher than weekend ridership.

## Initial Project Insights

The analysis provides several useful insights for the MetroFlow project:

- Evening hours show high passenger demand.
- Morning hours also show significant passenger demand.
- Certain stations have substantially higher total ridership than others.
- Passenger demand varies significantly between different dates.
- Weekday ridership is higher than weekend ridership.
- Thursday has the highest average ridership among the days analyzed.
- Sunday has the lowest average ridership.
- Off-peak periods have considerably lower average ridership.

These findings can be used as a starting point for:

- Identifying peak-hour congestion
- Crowd monitoring
- Station-wise crowd analysis
- Passenger demand forecasting
- Peak-hour prediction
- Train-frequency recommendations
- Future scheduling optimization

## Next Analysis Steps

The next stage should focus on more detailed station and time-based analysis, such as:

- Identifying the busiest station-hour combinations
- Analyzing station-wise peak hours
- Creating a station-hour heatmap
- Preparing features for passenger demand forecasting
- Evaluating whether additional entry/exit, train schedule, delay, occupancy, or realtime datasets are required for the remaining project milestones