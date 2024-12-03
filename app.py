import streamlit as st
import pandas as pd
import plotly.express as px
from process_data import clean_dataframe, calculate_training_recommendation
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
    """Style recommendations with black background and white text"""
    colors = {
        'more': 'background-color: #1e1e1e; color: white',  # Dark background for 'more'
        'same': 'background-color: #2d2d2d; color: white',  # Slightly lighter dark for 'same'
        'less': 'background-color: #3d3d3d; color: white'   # Even lighter dark for 'less'
    }
    return colors.get(val, '')

def sort_athletes(df):
    """Sort athletes by Top Player status and then alphabetically"""
    # Define Top Players
    top_players = [
        "Daniela Alvarez",
        "Stacy Reeves",
        "Hailey Hamlett",
        "Emma Glagau",
        "Maria Gonzalez",
        "Kaitlyn Bradley",
        "Ana Vergara",
        "Deni Konstantinova",
        "Tania Moreno",
        "Anete Namike",
        "Olivia Cliens",
        "Anhelina Khmil",
        "Allanis Navas",
        "Sofia Izuzquiza"
    ]
    
    # Create a new column for sorting
    df['sort_key'] = df['Athlete'].apply(lambda x: (0 if x in top_players else 1, x))
    
    # Sort by the tuple (top_player_status, name)
    df = df.sort_values('sort_key')
    
    # Drop the sorting column
    df = df.drop('sort_key', axis=1)
    
    return df

st.set_page_config(page_title="Beach Volleyball Load Management", layout="wide")

if not check_password():
    st.stop()

st.title("Beach Volleyball Load Management Dashboard")

try:
    # Read data from the data directory
    data_path = "data"
    data_files = [f for f in os.listdir(data_path) if f.endswith('.xlsx')]
    
    if not data_files:
        st.error("No Excel files found in the data directory")
        st.stop()
    
    # Process all files
    dfs = []
    for file in data_files:
        df = pd.read_excel(os.path.join(data_path, file))
        dfs.append(df)
    
    # Combine all data
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
    
    # Clean the combined data
    combined_df = clean_dataframe(combined_df)
    
    # Calculate recommendations
    results = []
    for athlete in combined_df['Athlete name'].unique():
        athlete_data = combined_df[combined_df['Athlete name'] == athlete]
        recent_data = athlete_data[athlete_data['Start date (dd.mm.yyyy)'] == 
                               athlete_data['Start date (dd.mm.yyyy)'].max()].iloc[0]
        
        rec, details = calculate_training_recommendation(athlete_data, recent_data)
        
        results.append({
            'Athlete': athlete,
            'Recommendation': rec,
            'ACWR': details['acwr'],
            'Acute_Load_Ratio': details['acute_ratio'],
            'HR_Min_Ratio': details['hr_ratio'],
            'Movement_Ratio': details['movement_ratio'],
            'Last Training': recent_data['Start date (dd.mm.yyyy)'],
            'Adjustment_Score': details['adjustment_score']
        })
    
    recommendations = pd.DataFrame(results)
    
    # Display recommendations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Recommendations")
        
        # Sort the recommendations
        recommendations = sort_athletes(recommendations)
        
        # Apply styling
        styled_recommendations = recommendations.style.applymap(
            color_recommendations, 
            subset=['Recommendation']
        ).set_properties(**{
            'background-color': '#1e1e1e',
            'color': 'white',
            'border': '1px solid #2d2d2d'
        })
        
        st.dataframe(styled_recommendations)
    
    with col2:
        st.subheader("ACWR Distribution")
        fig = px.scatter(recommendations, 
                       x='ACWR', 
                       y='Athlete',
                       color='Recommendation',
                       title='ACWR by Athlete')
        fig.add_vline(x=1.0, line_dash="dash", line_color="green")
        fig.add_vline(x=1.3, line_dash="dash", line_color="red")
        fig.update_layout(
            plot_bgcolor='#1e1e1e',
            paper_bgcolor='#1e1e1e',
            font_color='white'
        )
        st.plotly_chart(fig)
    
    # Individual athlete analysis
    st.subheader("Individual Athlete Analysis")
    selected_athlete = st.selectbox("Select Athlete", recommendations['Athlete'].unique())
    
    if selected_athlete:
        athlete_data = combined_df[combined_df['Athlete name'] == selected_athlete]
        
        # Show ACWR trend
        st.line_chart(athlete_data.set_index('Start date (dd.mm.yyyy)')['ACWR'])
        
        # Show recent metrics
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        with metrics_col1:
            st.metric("Latest ACWR", 
                     f"{recommendations[recommendations['Athlete'] == selected_athlete]['ACWR'].iloc[0]:.2f}")
        with metrics_col2:
            st.metric("HR Minutes (+80%)", 
                     f"{athlete_data['HR Min (+80%)'].iloc[-1]:.1f}")
        with metrics_col3:
            st.metric("Movement Load", 
                     f"{athlete_data['Movement load'].iloc[-1]:.1f}")

except Exception as e:
    st.error(f"Error processing data: {str(e)}")
    st.write("Please ensure that the data directory exists and contains valid FirstBeat Excel files")
