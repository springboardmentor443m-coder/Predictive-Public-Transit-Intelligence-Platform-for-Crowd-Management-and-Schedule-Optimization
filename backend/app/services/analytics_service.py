import io
import csv
from datetime import datetime, timezone
from typing import List
from app.schemas.analytics_schema import (
    AnalyticsSummary, LinePerformanceMetric, RidershipTrendPoint
)


class AnalyticsService:
    @staticmethod
    async def get_analytics_summary() -> AnalyticsSummary:
        trend_points = [
            RidershipTrendPoint(time_label="06:00", total_inflow=4200, total_outflow=3800, avg_density_pct=32.0),
            RidershipTrendPoint(time_label="07:00", total_inflow=12800, total_outflow=11200, avg_density_pct=58.5),
            RidershipTrendPoint(time_label="08:00", total_inflow=24500, total_outflow=22100, avg_density_pct=84.2),
            RidershipTrendPoint(time_label="09:00", total_inflow=28900, total_outflow=27400, avg_density_pct=88.7),
            RidershipTrendPoint(time_label="10:00", total_inflow=16400, total_outflow=17200, avg_density_pct=62.1),
            RidershipTrendPoint(time_label="11:00", total_inflow=11200, total_outflow=12000, avg_density_pct=48.0),
            RidershipTrendPoint(time_label="12:00", total_inflow=13500, total_outflow=13100, avg_density_pct=51.4),
            RidershipTrendPoint(time_label="13:00", total_inflow=14200, total_outflow=14000, avg_density_pct=53.0),
            RidershipTrendPoint(time_label="14:00", total_inflow=12900, total_outflow=13200, avg_density_pct=49.8),
            RidershipTrendPoint(time_label="15:00", total_inflow=15800, total_outflow=15200, avg_density_pct=57.2),
            RidershipTrendPoint(time_label="16:00", total_inflow=19800, total_outflow=18400, avg_density_pct=68.9),
            RidershipTrendPoint(time_label="17:00", total_inflow=29400, total_outflow=26900, avg_density_pct=89.4),
            RidershipTrendPoint(time_label="18:00", total_inflow=31200, total_outflow=29800, avg_density_pct=92.1),
            RidershipTrendPoint(time_label="19:00", total_inflow=22100, total_outflow=24200, avg_density_pct=74.0),
            RidershipTrendPoint(time_label="20:00", total_inflow=11500, total_outflow=13800, avg_density_pct=45.0),
        ]

        lines = [
            LinePerformanceMetric(
                line_name="Red Line",
                active_trains=14,
                on_time_performance_pct=96.4,
                avg_delay_minutes=1.2,
                total_daily_ridership=142800,
                peak_crowd_station="Central Terminal"
            ),
            LinePerformanceMetric(
                line_name="Blue Line",
                active_trains=12,
                on_time_performance_pct=93.8,
                avg_delay_minutes=2.4,
                total_daily_ridership=125600,
                peak_crowd_station="Stadium Arena"
            ),
        ]

        return AnalyticsSummary(
            total_daily_passengers=268400,
            overall_otp_percentage=95.1,
            active_trains_count=26,
            critical_incidents_today=3,
            peak_rush_hour="18:00 - 19:00",
            line_performances=lines,
            ridership_trends=trend_points
        )

    @staticmethod
    async def generate_csv_report() -> str:
        summary = await AnalyticsService.get_analytics_summary()
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["MetroFlow Operational Performance Summary Report"])
        writer.writerow(["Generated At", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")])
        writer.writerow([])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Daily Passengers", summary.total_daily_passengers])
        writer.writerow(["Overall OTP (%)", summary.overall_otp_percentage])
        writer.writerow(["Active Trains", summary.active_trains_count])
        writer.writerow(["Critical Incidents", summary.critical_incidents_today])
        writer.writerow(["Peak Rush Hour", summary.peak_rush_hour])
        writer.writerow([])
        writer.writerow(["Time Slot", "Inflow Passengers", "Outflow Passengers", "Avg Density (%)"])

        for pt in summary.ridership_trends:
            writer.writerow([pt.time_label, pt.total_inflow, pt.total_outflow, pt.avg_density_pct])

        return output.getvalue()


analytics_service = AnalyticsService()
