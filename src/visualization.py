import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

VISUALIZATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "visualizations")

plt.rcParams['figure.figsize'] = (14, 7)
plt.rcParams['figure.dpi'] = 100
plt.rcParams['font.size'] = 11

def plot_weekly_heatmap(df, save=True):
    """Plot weekly traffic heatmap."""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    if 'hour' in df.columns and 'day_of_week' in df.columns:
        pivot = df.pivot_table(values=df.select_dtypes(include=[np.number]).columns[0],
                               index='hour', columns='day_of_week', aggfunc='mean')
        day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        sns.heatmap(pivot, cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Entries/Exits'},
                    xticklabels=day_labels)
        ax.set_xlabel('Day of Week')
        ax.set_ylabel('Hour of Day')
        ax.set_title('NYC Subway Weekly Traffic Heatmap (2017-2021)')
    
    if save:
        plt.tight_layout()
        plt.savefig(os.path.join(VISUALIZATIONS_DIR, 'weekly_heatmap.png'), bbox_inches='tight')
        plt.close()
    return fig

def plot_station_ranking(df, top_n=20, save=True):
    """Plot top N stations by traffic."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    if 'station_name' in df.columns:
        rankings = df.groupby('station_name').sum(numeric_only=True).iloc[:, :3].sum(axis=1).nlargest(top_n)
    else:
        rankings = df.groupby('station_id').sum(numeric_only=True).iloc[:, :3].sum(axis=1).nlargest(top_n)
    
    rankings.plot(kind='barh', ax=ax, color='steelblue')
    ax.set_xlabel('Total Traffic')
    ax.set_ylabel('Station')
    ax.set_title(f'Top {top_n} Busiest Stations')
    ax.invert_yaxis()
    
    if save:
        plt.tight_layout()
        plt.savefig(os.path.join(VISUALIZATIONS_DIR, 'station_ranking.png'), bbox_inches='tight')
        plt.close()
    return fig

def plot_predictions_vs_actual(y_true, y_pred, save=True):
    """Plot model predictions vs actual values."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.scatter(y_true, y_pred, alpha=0.3, s=10, color='steelblue')
    ax.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
    ax.set_xlabel('Actual Traffic')
    ax.set_ylabel('Predicted Traffic')
    ax.set_title('Model Predictions vs Actual')
    
    if save:
        plt.tight_layout()
        plt.savefig(os.path.join(VISUALIZATIONS_DIR, 'predictions_vs_actual.png'), bbox_inches='tight')
        plt.close()
    return fig

def plot_schedule_comparison(df, save=True):
    """Plot current vs optimized schedule comparison."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    if 'hour' in df.columns and 'day_of_week' in df.columns:
        # Current traffic pattern
        current = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        pivot_current = current.pivot(index='hour', columns='day_of_week', values='count')
        axes[0].imshow(pivot_current.values, cmap='Blues', aspect='auto')
        axes[0].set_xticks(range(7))
        axes[0].set_xticklabels(day_names)
        axes[0].set_ylabel('Hour')
        axes[0].set_title('Current Traffic Pattern')
    
    if save:
        plt.tight_layout()
        plt.savefig(os.path.join(VISUALIZATIONS_DIR, 'schedule_comparison.png'), bbox_inches='tight')
        plt.close()
    return fig

def plot_monthly_trends(df, save=True):
    """Plot monthly trends."""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    if 'month' in df.columns:
        monthly = df.groupby('month').sum(numeric_only=True)
        numeric_cols = monthly.columns[:5]
        for col in numeric_cols:
            ax.plot(monthly.index, monthly[col], marker='o', label=col)
        ax.set_xlabel('Month')
        ax.set_ylabel('Total Traffic')
        ax.set_title('Monthly Traffic Trends')
        ax.legend()
    
    if save:
        plt.tight_layout()
        plt.savefig(os.path.join(VISUALIZATIONS_DIR, 'monthly_trends.png'), bbox_inches='tight')
        plt.close()
    return fig

def plot_day_comparison(df, save=True):
    """Compare weekday vs weekend traffic."""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    if 'day_of_week' in df.columns and 'hour' in df.columns:
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        weekday_avg = df[df['is_weekend'] == 0].groupby('hour')[df.select_dtypes(include=[np.number]).columns[:3]].mean()
        weekend_avg = df[df['is_weekend'] == 1].groupby('hour')[df.select_dtypes(include=[np.number]).columns[:3]].mean()
        
        weekday_avg.T.plot(ax=ax, label='Weekday', marker='o')
        weekend_avg.T.plot(ax=ax, label='Weekend', marker='s')
        ax.set_xlabel('Hour')
        ax.set_ylabel('Average Traffic')
        ax.set_title('Weekday vs Weekend Traffic Patterns')
        ax.legend()
    
    if save:
        plt.tight_layout()
        plt.savefig(os.path.join(VISUALIZATIONS_DIR, 'weekday_vs_weekend.png'), bbox_inches='tight')
        plt.close()
    return fig

def create_all_visualizations(df):
    """Create all visualizations at once."""
    os.makedirs(VISUALIZATIONS_DIR, exist_ok=True)
    
    print("Generating visualizations...")
    plot_weekly_heatmap(df)
    plot_station_ranking(df)
    plot_monthly_trends(df)
    plot_day_comparison(df)
    
    print(f"All visualizations saved to {VISUALIZATIONS_DIR}/")
