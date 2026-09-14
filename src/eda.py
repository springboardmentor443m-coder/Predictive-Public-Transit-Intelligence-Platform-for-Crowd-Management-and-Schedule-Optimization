import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['figure.dpi'] = 100
plt.rcParams['font.size'] = 10

VISUALIZATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "visualizations")

def summary_statistics(df):
    """Generate summary statistics for the dataset."""
    print("=" * 60)
    print("DATASET SUMMARY STATISTICS")
    print("=" * 60)
    print(f"\nShape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"\nData Types:\n{df.dtypes}")
    print(f"\nMissing Values:\n{df.isnull().sum()}")
    print(f"\nBasic Statistics:\n{df.describe()}")
    return df.describe()

def plot_station_traffic(df, station_name=None, top_n=20):
    """Plot traffic patterns for top stations."""
    if 'station_name' in df.columns:
        station_counts = df.groupby('station_name').sum(numeric_only=True).iloc[:, :5]
        top_stations = station_counts.sum(axis=1).nlargest(top_n).index
        df_filtered = df[df['station_name'].isin(top_stations)]
    else:
        df_filtered = df
    
    numeric_cols = df_filtered.select_dtypes(include=[np.number]).columns[:8]
    n_cols = len(numeric_cols)
    n_rows = (n_cols + 1) // 2
    fig, axes = plt.subplots(n_rows, 2, figsize=(16, 6 * n_rows))
    axes = np.array(axes).flatten()
    
    for i, col in enumerate(numeric_cols):
        ax = axes[i]
        if 'station_name' in df_filtered.columns:
            df_filtered.groupby('station_name')[col].mean().nlargest(15).plot(kind='barh', ax=ax)
        else:
            df_filtered[col].plot(kind='line', ax=ax)
        ax.set_title(f'Average {col} by Station')
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(VISUALIZATIONS_DIR, 'station_traffic.png'))
    plt.close()
    print("Station traffic plot saved to visualizations/station_traffic.png")

def plot_hourly_patterns(df):
    """Plot hourly entry/exit patterns."""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    if 'hour' in df.columns and 'datetime' in df.columns:
        hourly = df.groupby('hour')[df.select_dtypes(include=[np.number]).columns[:6]].mean()
        hourly.T.plot(ax=ax, marker='o')
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Average Entries/Exits')
        ax.set_title('Hourly Traffic Patterns')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig(os.path.join(VISUALIZATIONS_DIR, 'hourly_patterns.png'))
    plt.close()
    print("Hourly patterns plot saved to visualizations/hourly_patterns.png")

def plot_daily_patterns(df):
    """Plot daily traffic patterns."""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    if 'day_of_week' in df.columns:
        daily = df.groupby('day_of_week')[df.select_dtypes(include=[np.number]).columns[:6]].mean()
        daily.plot(ax=ax, marker='o')
        ax.set_xticks(range(7))
        ax.set_xticklabels(day_names)
        ax.set_xlabel('Day of Week')
        ax.set_ylabel('Average Entries/Exits')
        ax.set_title('Daily Traffic Patterns')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig(os.path.join(VISUALIZATIONS_DIR, 'daily_patterns.png'))
    plt.close()
    print("Daily patterns plot saved to visualizations/daily_patterns.png")

def plot_weekly_heatmap(df):
    """Create a heatmap of weekly traffic patterns."""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    if 'day_of_week' in df.columns and 'hour' in df.columns:
        pivot = df.pivot_table(values=df.select_dtypes(include=[np.number]).columns[0],
                               index='hour', columns='day_of_week', aggfunc='mean')
        sns.heatmap(pivot, cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Entries/Exits'})
        ax.set_xlabel('Day of Week (0=Mon, 6=Sun)')
        ax.set_ylabel('Hour')
        ax.set_title('Weekly Traffic Heatmap')
    
    plt.tight_layout()
    plt.savefig(os.path.join(VISUALIZATIONS_DIR, 'weekly_heatmap.png'))
    plt.close()
    print("Weekly heatmap saved to visualizations/weekly_heatmap.png")

def plot_monthly_trends(df):
    """Plot monthly trends."""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    if 'month' in df.columns:
        monthly = df.groupby('month')[df.select_dtypes(include=[np.number]).columns[:6]].mean()
        monthly.T.plot(ax=ax, marker='s')
        ax.set_xlabel('Month')
        ax.set_ylabel('Average Entries/Exits')
        ax.set_title('Monthly Traffic Trends (2017-2021)')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig(os.path.join(VISUALIZATIONS_DIR, 'monthly_trends.png'))
    plt.close()
    print("Monthly trends plot saved to visualizations/monthly_trends.png")

def generate_eda_report(df):
    """Generate complete EDA report with all plots."""
    os.makedirs(VISUALIZATIONS_DIR, exist_ok=True)
    print("\n" + "=" * 60)
    print("GENERATING EXPLORATORY DATA ANALYSIS REPORT")
    print("=" * 60)
    
    summary_statistics(df)
    plot_station_traffic(df)
    plot_hourly_patterns(df)
    plot_daily_patterns(df)
    plot_weekly_heatmap(df)
    plot_monthly_trends(df)
    
    print("\nEDA report complete! All visualizations saved to /visualizations")
