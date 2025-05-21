import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Category10, Spectral6
from bokeh.transform import cumsum
import math
from typing import List, Dict, Any

# API Configuration
API_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Game Mental Health Analysis",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS to make the app look better
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4257B2;
        text-align: center;
        margin-bottom: 2rem;
    }
    .subheader {
        font-size: 1.8rem;
        color: #5E6373;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .recommendation-box {
        background-color: #F0F2F6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stat-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .positive {
        background-color: #D4EDDA;
    }
    .negative {
        background-color: #F8D7DA;
    }
    .neutral {
        background-color: #E2E3E5;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 1rem;
        color: #6C757D;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
def fetch_games():
    """Fetch list of available games from the API"""
    try:
        response = requests.get(f"{API_URL}/games")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching games: {e}")
        return []

def fetch_game_analysis(game_name):
    """Fetch analysis for a specific game"""
    try:
        response = requests.get(f"{API_URL}/analyze/{game_name}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching game analysis: {e}")
        return None

def create_pie_chart(chart_data):
    """Create a Bokeh pie chart"""
    data = chart_data["data"]
    
    # Data preparation
    x = dict(zip(data["labels"], data["values"]))
    data = pd.DataFrame(dict(labels=data["labels"], values=data["values"]))
    
    data['angle'] = data['values']/data['values'].sum() * 2*math.pi
    data['color'] = Spectral6[:len(data)]
    
    # Create pie chart
    p = figure(height=350, title=chart_data["title"], toolbar_location=None,
               tools="hover", tooltips="@labels: @values%", x_range=(-0.5, 1.0))
    
    p.wedge(x=0, y=0, radius=0.4,
            start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
            line_color="white", fill_color='color', legend_field='labels', source=data)
    
    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None
    
    return p

def create_bar_chart(chart_data):
    """Create a Bokeh bar chart"""
    data = chart_data["data"]
    
    # Data preparation
    source = ColumnDataSource(data=dict(
        labels=data["labels"],
        values=data["values"],
        color=Category10[10][:len(data["labels"])]
    ))
    
    # Create bar chart
    p = figure(x_range=data["labels"], height=350, title=chart_data["title"],
               toolbar_location=None, tools="hover", tooltips="@labels: @values")
    
    p.vbar(x='labels', top='values', width=0.9, source=source, color='color')
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    
    # Rotate x-axis labels if there are many
    if len(data["labels"]) > 4:
        p.xaxis.major_label_orientation = math.pi/3
    
    return p

def render_charts(charts):
    """Render all charts from the analysis"""
    chart_objs = []
    
    for chart in charts:
        if chart["chart_type"] == "pie":
            chart_objs.append(create_pie_chart(chart))
        elif chart["chart_type"] == "bar":
            chart_objs.append(create_bar_chart(chart))
    
    # Display charts
    for i in range(0, len(chart_objs), 2):
        cols = st.columns(2)
        for j in range(2):
            if i+j < len(chart_objs):
                with cols[j]:
                    st.bokeh_chart(chart_objs[i+j], use_container_width=True)

# Main App
st.markdown('<h1 class="main-header">Game Mental Health Analysis</h1>', unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Settings")
games = fetch_games()

if not games:
    st.error("Unable to fetch games from the API. Make sure the API is running.")
    st.info("Start the API with: `python analyze_data.py api`")
    st.stop()

selected_game = st.sidebar.selectbox("Select a Game", games)

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    """
    This app analyzes the mental health impact of various games based on 
    recorded player sessions. The data is analyzed using AI to provide 
    evidence-based recommendations.
    """
)

# Main content
if selected_game:
    analysis = fetch_game_analysis(selected_game)
    
    if analysis:
        # Header and summary
        st.markdown(f'<h2 class="subheader">{selected_game} Analysis</h2>', unsafe_allow_html=True)
        st.markdown(analysis["summary"])
        
        # Mental Health Impact Stats
        st.markdown('<h3 class="subheader">Mental Health Impact</h3>', unsafe_allow_html=True)
        impact = analysis["mental_health_impact"]
        
        cols = st.columns(3)
        with cols[0]:
            st.markdown(f"""
            <div class="stat-card positive">
                <div class="metric-value">{impact["positive"]:.1f}%</div>
                <div class="metric-label">Positive Impact</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown(f"""
            <div class="stat-card negative">
                <div class="metric-value">{impact["negative"]:.1f}%</div>
                <div class="metric-label">Negative Impact</div>
            </div>
            """, unsafe_allow_html=True)
            
        with cols[2]:
            st.markdown(f"""
            <div class="stat-card neutral">
                <div class="metric-value">{impact["neutral"]:.1f}%</div>
                <div class="metric-label">Neutral Impact</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Visualizations
        st.markdown('<h3 class="subheader">Visualizations</h3>', unsafe_allow_html=True)
        render_charts(analysis["charts"])
        
        # Recommendations
        st.markdown('<h3 class="subheader">Recommendations</h3>', unsafe_allow_html=True)
        for i, rec in enumerate(analysis["recommendations"]):
            st.markdown(f"""
            <div class="recommendation-box">
                <strong>Recommendation {i+1}:</strong> {rec}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("Failed to fetch analysis. Please check if the API is running.")
else:
    st.info("Please select a game from the sidebar to see its analysis.")
