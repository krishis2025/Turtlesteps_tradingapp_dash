# pages/overview.py

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Database access (assuming utils/database.py is in the project root)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
import database as db

# Load config (assuming config.json is in the project root)
CONFIG_FILE = 'config.json'
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    config_path = os.path.join(project_root, 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    #print(f"Error: {CONFIG_FILE} not found for pages/overview.py. Using default settings.")
    config = { # Default minimal config
        "daily_risk": 550, "profit_target": 600, "max_trades_per_day": 6,
        "default_futures_type": "MES", "default_size": 5,
        "futures_types": {"ES": { "mf": 50 }, "MES": { "mf": 5 }},
        "pressing_sequence_multipliers": [1, 2, 1.5, 3],
        "database_name": "trades.db"
    }

# Register this page with Dash
dash.register_page(
    __name__,
    path='/overview',  # URL path for the dashboard overview page
    name='Dashboard Overview', # Name for navigation link in sidebar
    title='Trading Dashboard - Overview',
    description='High-level overview of trading performance.'
)

# --- Layout for the Dashboard Overview Page ---
layout = html.Div([
    html.H2("Overall Trading Performance Overview", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # Container for all the tiles
    html.Div(id='overview-tiles-container', style={
        'display': 'flex',
        'flexWrap': 'wrap',
        'justifyContent': 'center', # Center tiles horizontally
        'gap': '20px', # Space between tiles
        'padding': '20px',
        'backgroundColor': '#ffffff',
        'borderRadius': '8px',
        'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)'
    }, children=[
        # Example Tile 1: Total P&L
        html.Div(id='total-pnl-tile', style={
            'flex': '1 1 280px', # Flex-basis for tile width (adjust as needed)
            'minHeight': '150px',
            'backgroundColor': '#e3f2fd', # Light blue background
            'borderRadius': '8px',
            'padding': '20px',
            'textAlign': 'center',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'alignItems': 'center'
        }, children=[
            html.H3("Total Realized P&L", style={'marginBottom': '10px'}),
            html.P(id='total-pnl-value', style={'fontSize': '2.5em', 'fontWeight': 'bold', 'color': '#2196F3'})
        ]),

        # Example Tile 2: Win Rate
        html.Div(id='win-rate-tile', style={
            'flex': '1 1 280px',
            'minHeight': '150px',
            'backgroundColor': '#e8f5e9', # Light green background
            'borderRadius': '8px',
            'padding': '20px',
            'textAlign': 'center',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'alignItems': 'center'
        }, children=[
            html.H3("Win Rate", style={'marginBottom': '10px'}),
            html.P(id='win-rate-value', style={'fontSize': '2.5em', 'fontWeight': 'bold', 'color': '#4CAF50'})
        ]),

        # Example Tile 3: Total Trades
        html.Div(id='total-trades-tile', style={
            'flex': '1 1 280px',
            'minHeight': '150px',
            'backgroundColor': '#fff3e0', # Light orange background
            'borderRadius': '8px',
            'padding': '20px',
            'textAlign': 'center',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'alignItems': 'center'
        }, children=[
            html.H3("Avg Trades per day", style={'marginBottom': '10px'}),
            html.P(id='total-trades-value', style={'fontSize': '2.5em', 'fontWeight': 'bold', 'color': '#FF9800'})
        ]),

        # NEW TILE 4: Average Winning/Losing Trade
        html.Div(id='avg-win-loss-tile', style={
            'flex': '1 1 280px',
            'minHeight': '150px',
            'backgroundColor': '#e0f7fa', # Light cyan background
            'borderRadius': '8px',
            'padding': '20px',
            'textAlign': 'center',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'alignItems': 'center'
        }, children=[
            html.H3("Avg Win / Avg Loss", style={'marginBottom': '10px'}),
            html.P(id='avg-win-value', style={'fontSize': '1.5em', 'fontWeight': 'bold', 'color': '#4CAF50'}),
            html.P(id='avg-loss-value', style={'fontSize': '1.5em', 'fontWeight': 'bold', 'color': '#F44336'})
        ]),

        # NEW TILE 5: "Did Trade Come To You" Pie Chart
        html.Div(id='trade-came-pie-tile', style={
            'flex': '1 1 400px', # Slightly wider for pie chart
            'minHeight': '300px',
            'backgroundColor': '#ffffff',
            'borderRadius': '8px',
            'padding': '10px',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
        }, children=[
            html.H3("Trade Origination", style={'textAlign': 'center', 'marginBottom': '0px'}),
            dcc.Graph(id='trade-came-pie-chart', config={'displayModeBar': False}, style={'height': '250px'})
        ]),

        # NEW TILE 6: "Emotional State" Pie Chart
        html.Div(id='emotional-state-pie-tile', style={
            'flex': '1 1 400px', # Slightly wider for pie chart
            'minHeight': '300px',
            'backgroundColor': '#ffffff',
            'borderRadius': '8px',
            'padding': '10px',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
        }, children=[
            html.H3("Emotional State Breakdown", style={'textAlign': 'center', 'marginBottom': '0px'}),
            dcc.Graph(id='emotional-state-pie-chart', config={'displayModeBar': False}, style={'height': '250px'})
        ]),
        
        # You can add more tiles here for other KPIs like Avg P&L per Trade, Avg Win/Loss Size, etc.
    ]),

    # Hidden interval for initial data load
    dcc.Interval(id='overview-interval', interval=1000, n_intervals=0, max_intervals=1),
])

# pages/overview.py - Add this callback at the end of the file
# REPLACE its entire content with this:
@dash.callback(
    Output('total-pnl-value', 'children'),
    Output('win-rate-value', 'children'),
    Output('total-trades-value', 'children'), # Average Trades per Day
    Output('avg-win-value', 'children'), # New Output
    Output('avg-loss-value', 'children'), # New Output
    Output('trade-came-pie-chart', 'figure'), # Output for "Did Trade Come To You" pie chart
    Output('emotional-state-pie-chart', 'figure'), # Output for "Emotional State" pie chart
    Input('overview-interval', 'n_intervals'), # Trigger on initial page load
    prevent_initial_call=False # Allow to run once on initial load
)
def update_overview_kpis(n_intervals):
    if n_intervals == 0: # This callback will run once on page load
        try:
            db.initialize_db() # Ensure DB is initialized before fetching
            all_trades = db.fetch_all_trades_from_db() # Fetch all historical data
        except Exception as e:
            #print(f"Error fetching all historical trades for overview KPIs: {e}")
            # Return error state for all outputs
            return "$ N/A", "N/A%", "N/A", "$ N/A", "$ N/A", go.Figure(), go.Figure()

        if not all_trades:
            return "$0.00", "0.00%", "0.00", "$0.00", "$0.00", go.Figure(), go.Figure()

        df = pd.DataFrame(all_trades)
        df['Entry Time'] = pd.to_datetime(df['Entry Time'], errors='coerce')
        # Ensure valid data for calculations and pie charts, dropna early
        df = df.dropna(subset=['Entry Time', 'Realized P&L', 'Trade came to me', 'Emotional State'])

        df['Realized P&L'] = pd.to_numeric(df['Realized P&L'], errors='coerce').fillna(0)

        # If df becomes empty after cleaning (e.g., all relevant columns are NaN)
        if df.empty:
            #print("DEBUG Overview: DataFrame is empty after cleaning. Returning empty charts.")
            return "$0.00", "0.00%", "0.00", "$0.00", "$0.00", go.Figure(), go.Figure()

        # --- 1. Calculate General KPIs ---
        total_realized_pnl = df['Realized P&L'].sum()
        total_trades = len(df)
        
        winning_trades = df[df['Realized P&L'] > 0]
        losing_trades = df[df['Realized P&L'] <= 0]
        num_wins = len(winning_trades)
        
        win_rate = (num_wins / total_trades * 100) if total_trades > 0 else 0

        df['Date'] = df['Entry Time'].dt.date # Extract date part for unique days
        num_trading_days = df['Date'].nunique() # Count unique trading days
        
        avg_trades_per_day = (total_trades / num_trading_days) if num_trading_days > 0 else 0

        avg_win_size = (winning_trades['Realized P&L'].mean()) if num_wins > 0 else 0
        avg_loss_size = (losing_trades['Realized P&L'].mean()) if len(losing_trades) > 0 else 0


        # --- 2. Create Pie Chart for "Did Trade Come To You" ---
        trade_origination_value_counts_series = df['Trade came to me'].value_counts(dropna=False)
        
        # Handle case where value_counts might return an empty series
        if trade_origination_value_counts_series.empty:
            #print("DEBUG Overview: No data for 'Trade came to me' pie chart after value_counts.")
            trade_origination_pie_fig = go.Figure().update_layout(title="No Trade Origination Data") # Return empty figure
        else:
            trade_origination_counts = trade_origination_value_counts_series.reset_index()
            trade_origination_counts.columns = ['Category', 'Count']
            trade_origination_counts['Category'] = trade_origination_counts['Category'].fillna('Blank').replace('', 'Blank')
            
            #print(f"DEBUG Overview: Trade Origination Counts:\n{trade_origination_counts}")

            # NEW: Define color map for Trade Origination categories
            origination_color_map = {
                'Yes': '#4CAF50',   # Green
                'No': '#F44336',    # Red
                'Blank': '#9E9E9E'  # Grey
            }
            # Generate marker_colors list based on the order of labels in the data
            pie_colors_origination = [origination_color_map.get(cat, '#CCCCCC') for cat in trade_origination_counts['Category']] # Default to light grey if category not mapped


            trade_origination_pie_fig = go.Figure(data=[go.Pie(
                labels=trade_origination_counts['Category'],
                values=trade_origination_counts['Count'],
                hole=0.3, # Donut chart
                marker_colors= pie_colors_origination,
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )])
            trade_origination_pie_fig.update_layout(
                margin=dict(t=0, b=0, l=0, r=0), # Remove margins
                showlegend=True, # Show legend
                font={'color': '#333333'},
                paper_bgcolor='#ffffff', # CHANGED to white
                plot_bgcolor='#ffffff', # CHANGED to white
                height=250 # Control height within tile
            )

        # --- 3. Create Pie Chart for "Emotional State" ---
        emotional_state_value_counts_series = df['Emotional State'].value_counts(dropna=False)
        
        # Handle case where value_counts might return an empty series
        if emotional_state_value_counts_series.empty:
            #print("DEBUG Overview: No data for 'Emotional State' pie chart after value_counts.")
            emotional_state_pie_fig = go.Figure().update_layout(title="No Emotional State Data") # Return empty figure
        else:
            emotional_state_counts = emotional_state_value_counts_series.reset_index()
            emotional_state_counts.columns = ['Category', 'Count']
            
            emotional_state_counts['Category'] = emotional_state_counts['Category'].fillna('Blank').replace('', 'Blank')

            #print(f"DEBUG Overview: Emotional State Counts:\n{emotional_state_counts}")

            # NEW: Define a more comprehensive color map for Emotional State categories (example colors)
            emotional_state_color_map = {
                'Calm / Disciplined': '#4CAF50',     # Green
                'Get back losses': '#F44336',        # Red
                'FOMO': '#FF9800',                   # Orange
                'Fear of giving away profit': '#FFEB3B', # Yellow
                'Overconfidence': '#9C27B0',         # Purple
                'Frustration / Impatience': '#FF5722', # Deep Orange
                'Distracted': '#607D8B',             # Blue Grey
                'Blank': '#9E9E9E'                   # Grey
            }
            # Generate marker_colors list based on the order of labels in the data
            pie_colors_emotional_state = [emotional_state_color_map.get(cat, '#CCCCCC') for cat in emotional_state_counts['Category']] # Default to light grey if category not mapped

            emotional_state_pie_fig = go.Figure(data=[go.Pie(
                labels=emotional_state_counts['Category'],
                values=emotional_state_counts['Count'],
                hole=0.3, # Donut chart
                marker_colors=pie_colors_emotional_state, # Use dynamically generated colors
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )])            
            emotional_state_pie_fig.update_layout(
                margin=dict(t=0, b=0, l=0, r=0), # Remove margins
                showlegend=True, # Show legend
                font={'color': '#333333'},
                paper_bgcolor='#ffffff', # CHANGED to white
                plot_bgcolor='#ffffff', # CHANGED to white
                height=250 # Control height within tile
            )


        # Return all calculated KPIs and figures
        return (
            f"${total_realized_pnl:,.2f}",
            f"{win_rate:,.2f}%",
            f"{avg_trades_per_day:,.2f}",
            f"${avg_win_size:,.2f}",
            f"${abs(avg_loss_size):,.2f}", # Display average loss as positive
            trade_origination_pie_fig,
            emotional_state_pie_fig
        )
    return (
        dash.no_update, dash.no_update, dash.no_update, # P&L, Win Rate, Avg Trades
        dash.no_update, dash.no_update, # Avg Win/Loss
        dash.no_update, dash.no_update # Pie charts
    )