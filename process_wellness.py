import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def process_wellness_data(df):
    """Process raw wellness data and prepare for visualization"""
    # Convert timestamp to datetime if it isn't already
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Date'] = df['Timestamp'].dt.date
    
    # Ensure Name column is correctly handled
    if 'Name' not in df.columns:
        df = df.rename(columns={'Athlete': 'Name'})
    
    # List of wellness metrics - MUST match your Excel columns exactly
    wellness_metrics = [
        'Hours Slept',
        'Sleep Quality', 
        'Mood',
        'Energy',
        'Mental Alertness',
        'Muscle Soreness',
        'School Stress'
    ]
    
    # Verify all required columns exist
    missing_cols = [col for col in wellness_metrics if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
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
            if not athlete_calc_data.empty:
                metric_data = athlete_calc_data[metric].astype(float)
                stats[athlete][metric] = {
                    'mean': metric_data.mean() if not metric_data.empty else None,
                    'std': metric_data.std() if len(metric_data) > 1 else None
                }
            else:
                stats[athlete][metric] = {'mean': None, 'std': None}
    
    return display_data, stats, wellness_metrics
