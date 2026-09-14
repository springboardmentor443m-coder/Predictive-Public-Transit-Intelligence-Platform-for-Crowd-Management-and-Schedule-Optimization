import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

VISUALIZATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "visualizations")

class WeeklyScheduleAnalyzer:
    """Analyze weekly traffic patterns and generate schedule recommendations."""
    
    def __init__(self, df):
        self.df = df.copy()
        self.weekly_patterns = {}
        self.schedule_recommendations = {}
    
    def compute_weekly_aggregates(self):
        """Compute weekly aggregates for each station."""
        df = self.df.copy()
        
        if 'datetime' in df.columns:
            df['week_of_year'] = df['datetime'].dt.isocalendar().week.astype(int)
            df['day_of_week'] = df['datetime'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Aggregate by station and day of week
        if 'station_id' in df.columns and 'station_name' in df.columns:
            group_cols = ['station_id', 'station_name', 'day_of_week']
        elif 'station_id' in df.columns:
            group_cols = ['station_id', 'day_of_week']
        else:
            group_cols = ['day_of_week']
        agg_cols = [col for col in df.select_dtypes(include=[np.number]).columns if col not in group_cols]
        self.weekly_patterns = df.groupby(group_cols).agg({
                col: 'sum' for col in agg_cols
            }).reset_index()
        
        print(f"Weekly aggregates computed for {len(self.weekly_patterns)} station-day combinations")
        return self.weekly_patterns
    
    def get_peak_hours(self, station_id=None, day_of_week=None):
        """Identify peak hours for a given station and day."""
        df = self.df.copy()
        
        if station_id:
            df = df[df['station_id'] == station_id]
        if day_of_week is not None:
            df = df[df['day_of_week'] == day_of_week]
        
        if 'hour' in df.columns:
            hourly_avg = df.groupby('hour')[df.select_dtypes(include=[np.number]).columns].mean()
            peak_hours = hourly_avg.idxmax(axis=0)
            return peak_hours.to_dict()
        return {}
    
    def generate_weekly_schedule(self):
        """Generate optimal weekly schedule based on traffic patterns."""
        self.compute_weekly_aggregates()
        
        schedule = {}
        entry_col = 'entries' if 'entries' in self.weekly_patterns.columns else self.weekly_patterns.select_dtypes(include=[np.number]).columns[0]
        exit_col = 'exits' if 'exits' in self.weekly_patterns.columns else self.weekly_patterns.select_dtypes(include=[np.number]).columns[1] if len(self.weekly_patterns.select_dtypes(include=[np.number]).columns) > 1 else entry_col
        
        for day in range(7):
            day_data = self.weekly_patterns[self.weekly_patterns['day_of_week'] == day]
            
            day_info = {
                'day_name': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day],
                'total_entries': 0,
                'total_exits': 0,
                'peak_hour': None,
                'recommended_frequency': 'Normal',
                'station_count': len(day_data)
            }
            
            if day_data.empty:
                day_info['recommended_frequency'] = 'Reduced'
            else:
                day_info['total_entries'] = int(day_data[entry_col].sum()) if entry_col in day_data.columns else 0
                day_info['total_exits'] = int(day_data[exit_col].sum()) if exit_col in day_data.columns else 0
                
                if day_info['total_entries'] > 0:
                    day_info['peak_hour'] = 'Peak hours identified'
                
                if day >= 5:
                    day_info['recommended_frequency'] = 'Reduced'
                elif day_info['total_entries'] > 1000000:
                    day_info['recommended_frequency'] = 'High'
                else:
                    day_info['recommended_frequency'] = 'Normal'
            
            schedule[f'day_{day}'] = day_info
        
        self.schedule_recommendations = schedule
        return schedule
    
    def get_station_rankings(self):
        """Rank stations by total weekly traffic."""
        if 'station_name' in self.df.columns:
            rankings = self.df.groupby('station_name')[self.df.select_dtypes(include=[np.number]).columns].sum().sort_values(
                by=self.df.select_dtypes(include=[np.number]).columns[0], ascending=False
            )
        elif 'station_id' in self.df.columns:
            rankings = self.df.groupby('station_id')[self.df.select_dtypes(include=[np.number]).columns].sum().sort_values(
                by=self.df.select_dtypes(include=[np.number]).columns[0], ascending=False
            )
        else:
            return None
        return rankings.head(20)
    
    def weekend_vs_weekday_analysis(self):
        """Compare weekend vs weekday traffic."""
        df = self.df.copy()
        if 'is_weekend' not in df.columns and 'day_of_week' in df.columns:
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        if 'is_weekend' in df.columns:
            weekend = df[df['is_weekend'] == 1].select_dtypes(include=[np.number]).mean()
            weekday = df[df['is_weekend'] == 0].select_dtypes(include=[np.number]).mean()
            comparison = pd.DataFrame({
                'Weekend': weekend,
                'Weekday': weekday,
                'Difference': weekend - weekday
            })
            return comparison
        return None
    
    def generate_weekly_report(self):
        """Generate comprehensive weekly analysis report."""
        self.compute_weekly_aggregates()
        schedule = self.generate_weekly_schedule()
        rankings = self.get_station_rankings()
        comparison = self.weekend_vs_weekday_analysis()
        
        report = {
            'schedule': schedule,
            'top_stations': rankings,
            'weekend_vs_weekday': comparison,
            'peak_hours_by_day': {day: self.get_peak_hours(day_of_week=day) for day in range(7)}
        }
        
        print("\n" + "=" * 60)
        print("WEEKLY SCHEDULE ANALYSIS REPORT")
        print("=" * 60)
        for day, info in schedule.items():
            print(f"\n{info['day_name']}: {info['recommended_frequency']} frequency | "
                  f"Entries: {info['total_entries']:,.0f}")
        
        return report
