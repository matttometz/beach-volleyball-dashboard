import streamlit as st
import pandas as pd
import plotly.express as px
from process_data import clean_dataframe, calculate_training_recommendation
from process_wellness import process_wellness_data, create_wellness_display, style_wellness_display
import os

# Password protection
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    
    return True

def color_recommendations(val):
    """Style recommendations with muted colors"""
    colors = {
        'More': 'background-color: #009a00',  # Muted green
        'Same': 'background-color: #909090',  # Light gray
        'Less': 'background-color: #b00000'   # Muted red
    }
    return colors.get(val, '')

def sort_athletes(df):
    """Sort athletes by Top Player status and then alphabetically"""
    top_players = {
        "Daniela Alvarez", "Stacy Reeves", "Hailey Hamlett", "Emma Glagau",
        "Maria Gonzalez", "Kaitlyn Bradley", "Ana Vergara", "Deni Konstantinova",
        "Tania Moreno", "Anete Namike", "Olivia Clines", "Anhelina Khmil",
        "Allanis Navas", "Sofia Izuzquiza"
    }
    
    top_player_df = df[df['Athlete'].isin(top_players)].copy()
    other_players_df = df[~df['Athlete'].isin(top_players)].copy()
    
    top_player_df = top_player_df.sort_values('Athlete')
    other_players_df = other_players_df.sort_values('Athlete')
    
    return pd.concat([top_player_df, other_players_df]).reset_index(drop=True)

st.set_page_config(page_title="Beach Volleyball Load Management", layout="wide")

if not check_password():
    st.stop()

st.title("TCU Beach Volleyball Load Management Dashboard")

try:
    # Read and process FirstBeat data
    data_path = "data"
    data_files = [f for f in os.listdir(data_path) if f.endswith('.xlsx')]
    
    if not data_files:
        st.error("No Excel files found in the data directory")
        st.stop()
    
    dfs = []
    for file in data_files:
        df = pd.read_excel(os.path.join(data_path, file))
        dfs.append(df)
    
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Group by athlete and date
    grouped_cols = {
        'TRIMP (Index)': 'sum',
        'Movement load': 'sum',
        'Anaerobic threshold zone (hh:mm:ss)': 'sum',
        'High intensity training (hh:mm:ss)': 'sum',
        'Acute Training Load': 'last',
        'Chronic Training Load': 'last',
        'ACWR': 'last',
        'Training Status': 'last'
    }
    
    combined_df = combined_df.groupby(['Athlete name', 'Start date (dd.mm.yyyy)']).agg(grouped_cols).reset_index()
    combined_df = clean_dataframe(combined_df)
    
    # Calculate recommendations
    results = []
    for athlete in combined_df['Athlete name'].unique():
        athlete_data = combined_df[combined_df['Athlete name'] == athlete]
        recent_data = athlete_data[athlete_data['Start date (dd.mm.yyyy)'] == 
                               athlete_data['Start date (dd.mm.yyyy)'].max()].iloc[0]
        
        rec, details = calculate_training_recommendation(athlete_data, recent_data)
        formatted_date = recent_data['Start date (dd.mm.yyyy)'].strftime('%Y-%m-%d')
        
        # Only include necessary columns
        results.append({
            'Athlete': athlete,
            'Recommendation': rec,
            'Last Training': formatted_date
        })
    
    recommendations = pd.DataFrame(results)
    recommendations = sort_athletes(recommendations)
    
    # Display simplified recommendations table
    st.subheader("Current Recommendations (Top 14)")
    styled_recommendations = recommendations.style.applymap(
        color_recommendations, 
        subset=['Recommendation']
    )
    st.dataframe(
        styled_recommendations,
        column_config={
            'Athlete': st.column_config.Column(width='medium'),
            'Recommendation': st.column_config.Column(width='medium'),
            'Last Training': st.column_config.Column(width='medium')
        }
    )
    
    # Get the latest training date
    latest_date = recommendations['Last Training'].max()
    
    st.subheader("Printable Training Recommendations")
    
    # Create the data rows
    more_athletes = recommendations[recommendations['Recommendation'] == 'More']['Athlete'].tolist()
    same_athletes = recommendations[recommendations['Recommendation'] == 'Same']['Athlete'].tolist()
    less_athletes = recommendations[recommendations['Recommendation'] == 'Less']['Athlete'].tolist()
    
    max_length = max(len(more_athletes), len(same_athletes), len(less_athletes))
    
    # Create the data structure with title, headers, and data
    data = []
    
    # Add title row
    data.append([f'Training Recommendations based on data from {latest_date}', '', ''])
    
    # Add header row
    data.append(['More Training', 'Maintain', 'Less Training'])
    
    # Add athlete rows, preserving order
    for i in range(max_length):
        more_name = more_athletes[i] if i < len(more_athletes) else ''
        same_name = same_athletes[i] if i < len(same_athletes) else ''
        less_name = less_athletes[i] if i < len(less_athletes) else ''
        data.append([more_name, same_name, less_name])
    
    # Create DataFrame with proper headers for export
    categorized_df = pd.DataFrame(data, columns=['More Training', 'Maintain', 'Less Training'])
    
    # Display the combined DataFrame
    st.dataframe(
        categorized_df,
        hide_index=True
    )
    
    st.subheader("Weekly Wellness Overview")
    
    # Read wellness data
    wellness_path = "wellness_data"
    wellness_files = [f for f in os.listdir(wellness_path) if f.endswith('.xlsx')]
    
    if not wellness_files:
        st.error("No wellness data files found")
    else:
        try:
            # Debug section
            st.write("Found wellness file:", wellness_files[0])
            wellness_df = pd.read_excel(os.path.join(wellness_path, wellness_files[0]))
            st.write("Raw data shape:", wellness_df.shape)
            st.write("Columns:", wellness_df.columns.tolist())
            st.write("First few rows of raw data:")
            st.dataframe(wellness_df.head())
            
        except Exception as e:
            st.error(f"Error reading wellness data: {str(e)}")

except Exception as e:
    st.error(f"Error processing data: {str(e)}")
    st.write("Please ensure that the data directory exists and contains valid FirstBeat Excel files")
