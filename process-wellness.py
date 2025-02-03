import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def process_wellness_data(df):
    """Process raw wellness data and prepare for visualization"""
    # Convert timestamp to datetime if it isn't already
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Date'] = df['Timestamp'].dt.date
    
    # Rename Name column if needed
    if 'Name' not in df.columns:
        df = df.rename(columns={'Athlete': 'Name'})
    
    # List of wellness metrics
    wellness_metrics = [
        'Hours Slept',
        'Sleep Quality',
        'Mood',
        'Energy',
        'Mental Alertness',
        'Muscle Soreness',
        'School Stress'
    ]
    
    # Get the most recent date
    most_recent_date = df['Date'].max()
    
    # Calculate date ranges
    display_start = most_recent_date - timedelta(days=6)  # Last 7 days
    calc_start = display_start - timedelta(days=14)  # Previous 2 weeks for calculations
    
    # Split data into display and calculation periods
    display_data = df[df['Date'] >= display_start].copy()
    calc_data = df[(df['Date'] >= calc_start) & (df['Date'] < display_start)].copy()
    
    # Calculate stats for each athlete and metric
    stats = {}
    all_athletes = df['Name'].unique()
    
    for athlete in all_athletes:
        stats[athlete] = {}
        athlete_calc_data = calc_data[calc_data['Name'] == athlete]
        
        for metric in wellness_metrics:
            metric_data = athlete_calc_data[metric]
            stats[athlete][metric] = {
                'mean': metric_data.mean() if not metric_data.empty else None,
                'std': metric_data.std() if len(metric_data) > 1 else None
            }
    
    return display_data, stats, wellness_metrics

def calculate_color_code(value, mean, std):
    """Determine color coding based on standard deviations"""
    if pd.isna(value) or mean is None or std is None or std == 0:
        return 'background-color: #ffffff'  # White for missing data
    
    z_score = (value - mean) / std
    
    if z_score < -1:
        return 'background-color: #b00000'  # Red for below average
    elif z_score > 1:
        return 'background-color: #009a00'  # Green for above average
    else:
        return 'background-color: #909090'  # Gray for within range

def create_wellness_display(display_data, stats, wellness_metrics):
    """Create the wellness display DataFrame with color coding"""
    # Get unique dates and sort them
    dates = sorted(display_data['Date'].unique())
    all_athletes = sorted(display_data['Name'].unique())
    
    # Create DataFrame with multi-index
    index_tuples = [(athlete, metric) 
                    for athlete in all_athletes 
                    for metric in wellness_metrics]
    multi_idx = pd.MultiIndex.from_tuples(index_tuples, names=['Athlete', 'Metric'])
    display_df = pd.DataFrame(index=multi_idx, columns=dates)
    
    # Fill in the data
    for date in dates:
        day_data = display_data[display_data['Date'] == date]
        for athlete in all_athletes:
            athlete_data = day_data[day_data['Name'] == athlete]
            if not athlete_data.empty:
                for metric in wellness_metrics:
                    display_df.loc[(athlete, metric), date] = athlete_data[metric].iloc[0]
    
    # Calculate and add team averages
    team_avg_idx = pd.MultiIndex.from_product([['Team Average'], wellness_metrics])
    team_avg_df = pd.DataFrame(index=team_avg_idx, columns=dates)
    
    for date in dates:
        day_data = display_data[display_data['Date'] == date]
        for metric in wellness_metrics:
            team_avg_df.loc[('Team Average', metric), date] = day_data[metric].mean()
    
    # Combine team averages with individual data
    final_df = pd.concat([team_avg_df, display_df])
    
    return final_df

def style_wellness_display(df, stats):
    """Apply color coding to the wellness display"""
    def style_cell(value, athlete, metric):
        if athlete == 'Team Average':
            return ''  # No color coding for team averages
        if pd.isna(value):
            return 'background-color: #ffffff'
        
        athlete_stats = stats.get(athlete, {}).get(metric, {})
        mean = athlete_stats.get('mean')
        std = athlete_stats.get('std')
        
        return calculate_color_code(value, mean, std)
    
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    
    for (athlete, metric) in df.index:
        for col in df.columns:
            styles.loc[(athlete, metric), col] = style_cell(
                df.loc[(athlete, metric), col],
                athlete,
                metric
            )
    
    return styles
