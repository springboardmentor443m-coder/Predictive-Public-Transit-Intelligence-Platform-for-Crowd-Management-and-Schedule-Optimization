import pandas as pd
import numpy as np
from scipy.optimize import minimize, linear_sum_assignment
from datetime import datetime, timedelta
import os

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

class ScheduleOptimizer:
    """Optimize subway schedules based on predicted crowd levels."""
    
    def __init__(self, df=None):
        self.df = df.copy() if df is not None else None
        self.optimized_schedule = None
    
    def calculate_demand_profile(self, station_data):
        """Calculate hourly demand profile for a station."""
        if 'hour' in station_data.columns:
            hourly_demand = station_data.groupby('hour')[
                station_data.select_dtypes(include=[np.number]).columns[:3]
            ].mean()
        else:
            hourly_demand = station_data.select_dtypes(include=[np.number]).mean()
        return hourly_demand
    
    def optimize_train_frequency(self, station_id, day_of_week, demand_data):
        """Optimize train frequency for a specific station and day."""
        if 'hour' in demand_data.columns:
            hourly_demand = demand_data.groupby('hour').sum(numeric_only=True)
            demands = np.zeros(24)
            for h, val in hourly_demand.iloc[:, 0].items():
                if h < 24:
                    demands[h] = val
        else:
            demands = hourly_demand.values if len(hourly_demand) > 0 else np.ones(24) * 100
            if len(demands) < 24:
                padded = np.zeros(24)
                padded[:len(demands)] = demands
                demands = padded
        
        # Define frequency optimization
        # Objective: minimize total wait time while ensuring capacity
        hours = np.arange(24)
        
        # Capacity per train (passengers)
        capacity = 1500
        # Minimum frequency (trains per hour)
        min_freq = 2
        # Maximum frequency (trains per hour)
        max_freq = 10
        
        # Optimize frequency to match demand
        def objective(freq):
            # Minimize difference between supply and demand
            supply = freq * capacity
            return np.sum((supply - demands) ** 2 / (demands + 1))
        
        constraints = []
        for i, h in enumerate(hours):
            constraints.append({'type': 'ineq', 'fun': lambda f, d=demands[i]: f * capacity - d})
        
        # Simple optimization
        optimal_freq = np.clip(demands / capacity, min_freq, max_freq)
        
        schedule = {
            'station_id': station_id,
            'day_of_week': day_of_week,
            'day_name': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week],
            'optimal_frequencies': {int(h): round(f, 2) for h, f in zip(hours, optimal_freq)},
            'peak_hours': [],
            'off_peak_hours': [],
            'total_trains_needed': int(np.sum(optimal_freq))
        }
        
        # Identify peak and off-peak hours
        peak_threshold = np.percentile(demands, 75)
        for h, d in zip(hours, demands):
            if d >= peak_threshold:
                schedule['peak_hours'].append(int(h))
            else:
                schedule['off_peak_hours'].append(int(h))
        
        return schedule
    
    def optimize_network_schedule(self):
        """Optimize schedules across the entire network."""
        if self.df is None:
            raise ValueError("No data loaded. Initialize with data first.")
        
        df = self.df.copy()
        if 'hour' not in df.columns and 'datetime' in df.columns:
            df['hour'] = df['datetime'].dt.hour
        if 'day_of_week' not in df.columns and 'datetime' in df.columns:
            df['day_of_week'] = df['datetime'].dt.dayofweek
        
        station_ids = df['station_id'].unique() if 'station_id' in df.columns else [0]
        
        optimized_schedule = {}
        
        for day in range(7):
            day_schedules = []
            for station_id in station_ids[:50]:  # Limit to first 50 stations for performance
                station_data = df[(df['station_id'] == station_id) & (df['day_of_week'] == day)]
                if len(station_data) > 0:
                    station_schedule = self.optimize_train_frequency(station_id, day, station_data)
                    day_schedules.append(station_schedule)
            
            optimized_schedule[f'day_{day}'] = day_schedules
        
        self.optimized_schedule = optimized_schedule
        return optimized_schedule
    
    def calculate_resource_allocation(self):
        """Calculate optimal resource allocation across stations."""
        if self.df is None:
            raise ValueError("No data loaded.")
        
        df = self.df.copy()
        if 'station_name' in df.columns:
            station_traffic = df.groupby('station_name').sum(numeric_only=True)
        elif 'station_id' in df.columns:
            station_traffic = df.groupby('station_id').sum(numeric_only=True)
        else:
            return None
        
        # Normalize traffic to get allocation percentages
        total_traffic = station_traffic.sum().sum()
        allocation = (station_traffic / total_traffic * 100).round(2)
        
        # Rank stations by traffic
        ranking = station_traffic.sum(axis=1).sort_values(ascending=False)
        
        resource_plan = {
            'total_stations': len(station_traffic),
            'total_traffic': int(total_traffic),
            'top_10_stations': ranking.head(10).to_dict(),
            'allocation_percentages': allocation.to_dict() if len(allocation.columns) > 0 else {},
            'recommended_staff_allocation': (ranking / ranking.sum() * 100).round(1).to_dict()
        }
        
        return resource_plan
    
    def generate_schedule_report(self):
        """Generate comprehensive schedule optimization report."""
        if self.df is None:
            raise ValueError("No data loaded.")
        
        schedule = self.optimize_network_schedule()
        resources = self.calculate_resource_allocation()
        
        report = {
            'schedule': schedule,
            'resources': resources,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_stations': len(self.df['station_id'].unique()) if 'station_id' in self.df.columns else 1,
                'date_range': '2017-2021',
                'optimal_days': {day: len(schedule[f'day_{day}']) for day in range(7)}
            }
        }
        
        print("\n" + "=" * 60)
        print("SCHEDULE OPTIMIZATION REPORT")
        print("=" * 60)
        print(f"Total Stations: {report['summary']['total_stations']}")
        for day, count in report['summary']['optimal_days'].items():
            print(f"  Day {day}: {count} stations optimized")
        
        return report
    
    def save_schedule(self, filepath=None):
        """Save the optimized schedule to CSV."""
        if self.optimized_schedule is None:
            self.optimize_network_schedule()
        
        os.makedirs(MODELS_DIR, exist_ok=True)
        if filepath is None:
            filepath = os.path.join(MODELS_DIR, 'optimized_schedule.csv')
        
        # Flatten schedule for CSV
        rows = []
        for day, schedules in self.optimized_schedule.items():
            for s in schedules:
                rows.append(s)
        
        pd.DataFrame(rows).to_csv(filepath, index=False)
        print(f"Optimized schedule saved to {filepath}")
