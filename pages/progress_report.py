

# pages/progress_report.py

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta # Added timedelta

# Database access
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
import database as db

# Load config
CONFIG_FILE = 'config.json'
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    config_path = os.path.join(project_root, 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    config = {"daily_risk": 550, "profit_target": 600, "max_trades_per_day": 6, "default_futures_type": "MES", "default_size": 5, "futures_types": {"ES": { "mf": 50 }, "MES": { "mf": 5 }}, "pressing_sequence_multipliers": [1, 2, 1.5, 3], "database_name": "trades.db"}


# Register this page
dash.register_page(
    __name__,
    path='/progress-report',  # URL path for this page
    name='Progress Report', # Name for navigation link
    title='Trading Dashboard - Progress Report',
    description='Track progress on trading behaviors over time.'
)

# --- Layout for the Progress Report Page ---
layout = html.Div([
    html.H2("Trading Behavior Progress Report", style={'textAlign': 'center', 'marginBottom': '20px'}),

    # Date Range Filter for the entire report
    html.Div([
        html.Label("Report Date Range:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.DatePickerRange(
            id='progress-date-range-picker',
            start_date_placeholder_text="Start Date",
            end_date_placeholder_text="End Date",
            display_format='MM-DD-YYYY',
            month_format='MMMM Y',
            updatemode='bothdates',
            style={'marginRight': '15px'}
        ),
    ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '30px', 'width': '100%'}),

    # Line Charts for Weekly % Trends
    html.Div(style={
        'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'gap': '20px', 'padding': '20px',
        'backgroundColor': '#ffffff', 'borderRadius': '8px', 'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)',
        'marginBottom': '30px'
    }, children=[
        html.Div([
            html.H3("Trade Origination Progress (Weekly % 'Yes')", style={'textAlign': 'center', 'marginBottom': '10px'}),
            dcc.Graph(id='trade-origination-progress-chart', config={'displayModeBar': False}, style={'height': '300px', 'width': '100%'})
        ], style={'flex': '1 1 450px', 'minHeight': '350px', 'padding': '15px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.05)', 'borderRadius': '8px', 'backgroundColor': '#f8f8f8'}),

        html.Div([
            html.H3("Entry Quality Progress (Weekly % Calm/Patient)", style={'textAlign': 'center', 'marginBottom': '10px'}),
            dcc.Graph(id='entry-quality-progress-chart', config={'displayModeBar': False}, style={'height': '300px', 'width': '100%'})
        ], style={'flex': '1 1 450px', 'minHeight': '350px', 'padding': '15px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.05)', 'borderRadius': '8px', 'backgroundColor': '#f8f8f8'}),

        html.Div([
            html.H3("Emotional State Progress (Weekly % Calm/Disciplined)", style={'textAlign': 'center', 'marginBottom': '10px'}),
            dcc.Graph(id='emotional-state-progress-chart', config={'displayModeBar': False}, style={'height': '300px', 'width': '100%'})
        ], style={'flex': '1 1 450px', 'minHeight': '350px', 'padding': '15px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.05)', 'borderRadius': '8px', 'backgroundColor': '#f8f8f8'}),
        
        # Optional: Negative Trend (Impulsive/FOMO)
        html.Div([
            html.H3("Negative Behaviors Trend (Weekly %)", style={'textAlign': 'center', 'marginBottom': '10px'}),
            dcc.Graph(id='negative-behaviors-trend-chart', config={'displayModeBar': False}, style={'height': '300px', 'width': '100%'})
        ], style={'flex': '1 1 450px', 'minHeight': '350px', 'padding': '15px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.05)', 'borderRadius': '8px', 'backgroundColor': '#f8f8f8'}),
    ]),

    # Bar Charts for Percentage Distributions
    html.Div(style={
        'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'gap': '20px', 'padding': '20px',
        'backgroundColor': '#ffffff', 'borderRadius': '8px', 'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)'
    }, children=[
        html.Div([
            html.H3("Entry Quality Distribution (%)", style={'textAlign': 'center', 'marginBottom': '10px'}),
            dcc.Graph(id='entry-quality-distribution-chart', config={'displayModeBar': False}, style={'height': '350px', 'width': '100%'})
        ], style={'flex': '1 1 550px', 'minHeight': '400px', 'padding': '15px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.05)', 'borderRadius': '8px', 'backgroundColor': '#f8f8f8'}),

        html.Div([
            html.H3("Emotional State Distribution (%)", style={'textAlign': 'center', 'marginBottom': '10px'}),
            dcc.Graph(id='emotional-state-distribution-chart', config={'displayModeBar': False}, style={'height': '350px', 'width': '100%'})
        ], style={'flex': '1 1 550px', 'minHeight': '400px', 'padding': '15px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.05)', 'borderRadius': '8px', 'backgroundColor': '#f8f8f8'}),
    ]),

    # Hidden interval for initial data load
    dcc.Interval(id='progress-report-interval', interval=1000, n_intervals=0, max_intervals=1),
])

# pages/progress_report.py - Add these helper functions after the 'layout' definition

def _process_data_for_progress_report(df, start_date, end_date):
    """
    Cleans and filters the DataFrame for the progress report.
    Converts Entry Time to datetime and Realized P&L to float.
    Filters by date range.
    """
    df['Entry Time'] = pd.to_datetime(df['Entry Time'], errors='coerce')
    df = df.dropna(subset=['Entry Time', 'Realized P&L']) # Drop rows where essential data is missing
    df['Realized P&L'] = pd.to_numeric(df['Realized P&L'], errors='coerce').fillna(0).astype(float)
    df['Date'] = df['Entry Time'].dt.date # Extract just the date part for grouping

    # Filter by date range
    if start_date and end_date:
        start_datetime = pd.to_datetime(start_date).date()
        end_datetime = pd.to_datetime(end_date).date()
        df = df[(df['Date'] >= start_datetime) & (df['Date'] <= end_datetime)].copy() # Use .copy() to avoid SettingWithCopyWarning
    
    return df

def _calculate_weekly_behavior_trends(df):
    """
    Calculates weekly percentages for desired and negative behaviors.
    Returns: df with 'Week_Start' and percentages.
    """
    if df.empty:
        return pd.DataFrame()

    # Calculate ISO week and year
    df['Week_Start'] = df['Entry Time'].apply(lambda x: x - timedelta(days=x.weekday())) # Monday of the week
    df['Week_Start'] = df['Week_Start'].dt.date

    weekly_data = df.groupby('Week_Start').agg(
        Total_Trades=('Trade #', 'count'),
        Trades_Came_Yes=('Trade came to me', lambda x: (x == 'Yes').sum()),
        Trades_Calm_Patient=('Entry Quality', lambda x: ((x == 'Calm') | (x == 'Calm / Waited Patiently')).sum()),
        Trades_Calm_Disciplined=('Emotional State', lambda x: (x == 'Calm').sum()),
        Trades_Impulsive_FOMO=('Entry Quality', lambda x: ((x == 'Impulsive / FOMO') | (x == 'Forced / Overtraded')).sum()),
        Trades_GetBackLosses=('Emotional State', lambda x: (x == 'Get back losses').sum())
    ).reset_index()

    # Calculate percentages
    weekly_data['%_Came_Yes'] = (weekly_data['Trades_Came_Yes'] / weekly_data['Total_Trades'] * 100).fillna(0)
    weekly_data['%_Calm_Patient'] = (weekly_data['Trades_Calm_Patient'] / weekly_data['Total_Trades'] * 100).fillna(0)
    weekly_data['%_Calm_Disciplined'] = (weekly_data['Trades_Calm_Disciplined'] / weekly_data['Total_Trades'] * 100).fillna(0)
    weekly_data['%_Impulsive_FOMO'] = (weekly_data['Trades_Impulsive_FOMO'] / weekly_data['Total_Trades'] * 100).fillna(0)
    weekly_data['%_GetBackLosses'] = (weekly_data['Trades_GetBackLosses'] / weekly_data['Total_Trades'] * 100).fillna(0)
    
    weekly_data['Week_Start'] = pd.to_datetime(weekly_data['Week_Start']) # NEW: Convert Week_Start to datetime object
    return weekly_data.sort_values(by='Week_Start')

# def _create_line_chart_trend(df_weekly, y_col, title, color):
#     """Creates a line chart for weekly behavior trends."""
#     fig = go.Figure()
#     if not df_weekly.empty:
#         print(f"DEBUG Trend: Plotting '{title}'")
#         print(f"DEBUG Trend: df_weekly head:\n{df_weekly.head()}")
#         print(f"DEBUG Trend: df_weekly info:")
#         fig.add_trace(go.Scatter(x=df_weekly['Week_Start'], y=df_weekly[y_col], mode='lines+markers', line=dict(color=color)))
#         print(f"DEBUG Trend: Y-column '{y_col}' data head:\n{df_weekly[y_col].head()}")
#         print(f"DEBUG Trend: Y-column '{y_col}' data dtype: {df_weekly[y_col].dtype}")
#         print(f"DEBUG Trend: X-column 'Week_Start' data head:\n{df_weekly['Week_Start'].head()}")
#         print(f"DEBUG Trend: X-column 'Week_Start' data dtype: {df_weekly['Week_Start'].dtype}")

#     fig.update_layout(
#         title=title,
#         xaxis_title='Week Start Date',
#         yaxis_title='Percentage (%)',
#         yaxis_range=[0, 100],
#         plot_bgcolor='#f8f8f8', # Match tile background
#         paper_bgcolor='transparent', # Match tile background
#         font={'color': '#333333'},
#         margin=dict(t=40, b=30, l=40, r=20),
#     )
#     return fig

# Locate this section in pages/overview.py:
# def _create_line_chart_trend(df_weekly, y_col, title, color):
#     """Creates a line chart for weekly behavior trends."""
#     ...

# Locate this section in pages/overview.py, inside _create_line_chart_trend function:
def _create_line_chart_trend(df_weekly, y_col, title, color):
    """Creates a line chart for weekly behavior trends."""
    fig = go.Figure()
    if not df_weekly.empty:
        # Debug prints (keep them for now)
        print(f"DEBUG Trend: Plotting '{title}'")
        print(f"DEBUG Trend: df_weekly head:\n{df_weekly.head()}")
        print(f"DEBUG Trend: df_weekly info:")
        df_weekly.info()
        print(f"DEBUG Trend: Y-column '{y_col}' data head:\n{df_weekly[y_col].head()}")
        print(f"DEBUG Trend: Y-column '{y_col}' data dtype: {df_weekly[y_col].dtype}")
        print(f"DEBUG Trend: X-column 'Week_Start' data head:\n{df_weekly['Week_Start'].head()}")
        print(f"DEBUG Trend: X-column 'Week_Start' data dtype: {df_weekly['Week_Start'].dtype}")

        # NEW: Ensure Week_Start is clean before adding trace
        df_weekly_clean = df_weekly.dropna(subset=['Week_Start']).copy() # Drop any rows where Week_Start is NaT
        
        # If df_weekly_clean becomes empty after dropping NaTs, return an empty figure
        if df_weekly_clean.empty:
            print(f"DEBUG Trend: df_weekly_clean is empty after dropping NaT from 'Week_Start'. Returning empty figure for '{title}'.")
            return fig.update_layout(title=f"{title} (No Valid Date Data)")

        # Debug print for clean data
        print(f"DEBUG Trend: Cleaned df_weekly_clean head (after dropping NaT from Week_Start):\n{df_weekly_clean.head()}")


        fig.add_trace(go.Scatter(
            x=df_weekly_clean['Week_Start'], # Use the cleaned DataFrame
            y=df_weekly_clean[y_col],         # Use the cleaned DataFrame
            mode='lines+markers',
            line=dict(color='#3CB371', width=3), # Original -> dict(color='purple', width=5), # Aggressive color and width for debugging
            marker=dict(size=5, color='black'), # Large black markers
            name=y_col
        ))
    
    print("before udpate_layout")
    # fig.update_layout(
    #     title=title,
    #     xaxis_title='Week Start Date',
    #     yaxis_title='Percentage (%)',
    #     yaxis_range=[0, 100],
    #     # Ensure tickformat is only applied to clean datetime data
    #     xaxis={'showgrid': True, 'zeroline': True, 'tickformat': '%Y-%m-%d'}, # Explicit grid, zeroline, and date format
    #     yaxis={'showgrid': True, 'zeroline': True},
    #     plot_bgcolor='lightgray', # Very distinct plot background for debugging
    #     paper_bgcolor='transparent', # Match tile background
    #     font={'color': '#333333'},
    #     margin=dict(t=40, b=30, l=40, r=20),
    # )
    fig.update_layout(
        title=title,
        xaxis_title='Week Start Date',
        yaxis_title='Percentage (%)',
        yaxis_range=[0, 100],
        # Ensure tickformat is only applied to clean datetime data
        xaxis={'showgrid': True, 'zeroline': True, 'tickformat': '%Y-%m-%d'}, # Explicit grid, zeroline, and date format
        yaxis={'showgrid': True, 'zeroline': True},
        plot_bgcolor='white', #'lightgray', # Very distinct plot background for debugging
        paper_bgcolor='white', #'rgba(0,0,0,0)',  # ✅ Fully transparent
        font={'color': '#333333'},
        margin=dict(t=40, b=30, l=40, r=20),
    )
    
    print("after_update layout")
    return fig
    

def _calculate_categorical_distributions(df, category_col):
    """Calculates percentage distribution for a given categorical column."""
    if df.empty or category_col not in df.columns or df[category_col].isnull().all() or (df[category_col] == '').all():
        return pd.DataFrame()

    counts_series = df[category_col].value_counts(dropna=False)
    df_counts = counts_series.reset_index()
    df_counts.columns = ['Category', 'Count']
    df_counts['Category'] = df_counts['Category'].fillna('Blank').replace('', 'Blank')
    
    df_counts['Percentage'] = (df_counts['Count'] / df_counts['Count'].sum()) * 100
    
    return df_counts.sort_values(by='Percentage', ascending=False)

def _create_bar_chart_distribution(df_distribution, title, color_map=None):
    """Creates a bar chart for categorical distributions."""
    fig = go.Figure()
    if not df_distribution.empty:
        # Use existing color map or default if not provided
        colors = [color_map.get(cat, '#CCCCCC') for cat in df_distribution['Category']] if color_map else '#3498db'

        fig.add_trace(go.Bar(
            x=df_distribution['Category'],
            y=df_distribution['Percentage'],
            marker_color=colors,
            text=df_distribution['Percentage'],
            texttemplate="%{y:,.1f}%",
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Percentage: %{y:,.1f}%<br>Count: %{customdata}<extra></extra>',
            customdata=df_distribution['Count']
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Category',
        yaxis_title='Percentage (%)',
        yaxis_range=[0, 100],
        plot_bgcolor='#f8f8f8',
        paper_bgcolor='rgba(0,0,0,0)',  # ✅ Fully transparent
        font={'color': '#333333'},
        margin=dict(t=40, b=30, l=40, r=20),
    )
    return fig

# pages/progress_report.py - Add this main callback at the very end of the file


############################################################################
# Call Back
###########################################################################

@dash.callback(
    Output('trade-origination-progress-chart', 'figure'),
    Output('entry-quality-progress-chart', 'figure'),
    Output('emotional-state-progress-chart', 'figure'),
    Output('negative-behaviors-trend-chart', 'figure'),
    Output('entry-quality-distribution-chart', 'figure'),
    Output('emotional-state-distribution-chart', 'figure'),
    Input('progress-report-interval', 'n_intervals'), # Initial load trigger
    Input('progress-date-range-picker', 'start_date'),
    Input('progress-date-range-picker', 'end_date'),
    prevent_initial_call=False
)
def update_progress_report(n_intervals, start_date, end_date):
    if n_intervals == 0 and not start_date and not end_date:
        # On initial load, if no dates are pre-selected, set a default range (e.g., last 6 months)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6*30) # Approx 6 months
        # Note: This default range is only applied if start_date/end_date are None on initial load.
        # The PickerRange will then update, triggering the callback again with real dates.

    # Fetch all historical data
    try:
        db.initialize_db()
        all_trades = db.fetch_all_trades_from_db()
    except Exception as e:
        print(f"Error fetching all historical trades for Progress Report: {e}")
        # Return empty figures on error
        return go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure()

    if not all_trades:
        # Return empty figures if no data
        return go.Figure().update_layout(title="No Trade Data"), \
               go.Figure().update_layout(title="No Trade Data"), \
               go.Figure().update_layout(title="No Trade Data"), \
               go.Figure().update_layout(title="No Trade Data"), \
               go.Figure().update_layout(title="No Trade Data"), \
               go.Figure().update_layout(title="No Trade Data")

    df = pd.DataFrame(all_trades)
    df_processed = _process_data_for_progress_report(df, start_date, end_date)

    if df_processed.empty:
        print("DEBUG Progress Report: DataFrame is empty after date range filtering.")
        return go.Figure().update_layout(title="No Data for Selected Range"), \
               go.Figure().update_layout(title="No Data for Selected Range"), \
               go.Figure().update_layout(title="No Data for Selected Range"), \
               go.Figure().update_layout(title="No Data for Selected Range"), \
               go.Figure().update_layout(title="No Data for Selected Range"), \
               go.Figure().update_layout(title="No Data for Selected Range")

    # --- Weekly Trend Charts ---
    weekly_trends_df = _calculate_weekly_behavior_trends(df_processed)
    

    trade_origination_fig = _create_line_chart_trend(weekly_trends_df, '%_Came_Yes', "Trade Origination Progress (Weekly % 'Yes')", '#3498db')
    print("test2")

    entry_quality_fig = _create_line_chart_trend(weekly_trends_df, '%_Calm_Patient', "Entry Quality Progress (Weekly % Calm/Patient)", '#2ecc71')
    emotional_state_fig = _create_line_chart_trend(weekly_trends_df, '%_Calm_Disciplined', "Emotional State Progress (Weekly % Calm/Disciplined)", '#9b59b6')
    
    # Negative Trends
    negative_behaviors_fig = go.Figure()
    if not weekly_trends_df.empty:
        negative_behaviors_fig.add_trace(go.Scatter(x=weekly_trends_df['Week_Start'], y=weekly_trends_df['%_Impulsive_FOMO'], mode='lines+markers', name='% Impulsive/FOMO', line=dict(color='#e74c3c')))
        negative_behaviors_fig.add_trace(go.Scatter(x=weekly_trends_df['Week_Start'], y=weekly_trends_df['%_GetBackLosses'], mode='lines+markers', name='% Get Back Losses', line=dict(color='#e67e22')))
        negative_behaviors_fig.update_layout(
            title="Negative Behaviors Trend (Weekly %)",
            xaxis_title='Week Start Date',
            yaxis_title='Percentage (%)',
            yaxis_range=[0, 100],
            plot_bgcolor='#f8f8f8',
            paper_bgcolor='rgba(0,0,0,0)',  # ✅ Fully transparent
            font={'color': '#333333'},
            margin=dict(t=40, b=30, l=40, r=20),
            legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.7)'),
        )
    else:
        negative_behaviors_fig.update_layout(title="No Negative Behaviors Data")


    # --- Bar Charts for Percentage Distributions ---
    entry_quality_dist_df = _calculate_categorical_distributions(df_processed, 'Entry Quality')
    emotional_state_dist_df = _calculate_categorical_distributions(df_processed, 'Emotional State')

    # Color maps for distribution bar charts
    entry_quality_color_map = {
        'Waited Patiently': '#2ecc71', 'Calm / Standard': '#3498db', 'Impulsive / FOMO': '#e74c3c',
        'Hesitant / Missed': '#f1c40f', 'Forced / Overtraded': '#c0392b', 'Blank': '#9e9e9e'
    }
    emotional_state_color_map = {
        'Calm / Disciplined': '#2ecc71', 'Get back losses': '#e74c3c', 'FOMO': '#f39c12',
        'Fear of giving away profit': '#f1c40f', 'Overconfidence': '#9b59b6',
        'Frustration / Impatience': '#d35400', 'Distracted': '#7f8c8d', 'Blank': '#9e9e9d'
    }

    entry_quality_dist_fig = _create_bar_chart_distribution(entry_quality_dist_df, "Entry Quality Distribution (%)", entry_quality_color_map)
    emotional_state_dist_fig = _create_bar_chart_distribution(emotional_state_dist_df, "Emotional State Distribution (%)", emotional_state_color_map)

    return (
        trade_origination_fig,
        entry_quality_fig,
        emotional_state_fig,
        negative_behaviors_fig,
        entry_quality_dist_fig,
        emotional_state_dist_fig
    )