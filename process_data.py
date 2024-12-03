import pandas as pd
import numpy as np

def clean_dataframe(df):
    """Clean and process raw FirstBeat data"""
    columns_to_keep = [
        'Athlete name',
        'Start date (dd.mm.yyyy)',
        'TRIMP (Index)',
        'Movement load',
        'Anaerobic threshold zone (hh:mm:ss)',
        'High intensity training (hh:mm:ss)',
        'Acute Training Load',
        'Chronic Training Load',
        'ACWR',
        'Training Status'
    ]
    
    df = df[columns_to_keep].copy()
    
    # Convert time columns to minutes
    time_columns = [
        'Anaerobic threshold zone (hh:mm:ss)',
        'High intensity training (hh:mm:ss)'
    ]
    
    for col in time_columns:
        df[col] = pd.to_timedelta(df[col]).dt.total_seconds() / 60
    
    # Calculate HR Min (+80%)
    df['HR Min (+80%)'] = df['Anaerobic threshold zone (hh:mm:ss)'] + df['High intensity training (hh:mm:ss)']
    
    # Remove outliers
    df = df[
        (df['TRIMP (Index)'] >= 50) &
        (df['Movement load'] >= 50)
    ]
    
    return df

def calculate_training_recommendation(athlete_data, recent_data):
    """Calculate training recommendations based on athlete data"""
    numeric_cols = ['Acute Training Load', 'HR Min (+80%)', 'Movement load']
    athlete_means = athlete_data[numeric_cols].mean()
    
    acwr = recent_data['ACWR']
    if pd.isna(acwr):
        base_rec = "same"
    elif acwr < 1.0:
        base_rec = "more"
    elif acwr > 1.3:
        base_rec = "less"
    else:
        base_rec = "same"
    
    acute_load_ratio = recent_data['Acute Training Load'] / athlete_means['Acute Training Load']
    hr_min_ratio = recent_data['HR Min (+80%)'] / athlete_means['HR Min (+80%)']
    movement_ratio = recent_data['Movement load'] / athlete_means['Movement load']
    
    adjustment_score = (
        0.4 * acute_load_ratio +
        0.3 * hr_min_ratio +
        0.3 * movement_ratio
    )
    
    final_rec = base_rec
    if base_rec == "same":
        if adjustment_score < 0.8:
            final_rec = "more"
        elif adjustment_score > 1.2:
            final_rec = "less"
            
    return final_rec, {
        'base_rec': base_rec,
        'acwr': acwr,
        'adjustment_score': adjustment_score,
        'acute_ratio': acute_load_ratio,
        'hr_ratio': hr_min_ratio,
        'movement_ratio': movement_ratio
    }
