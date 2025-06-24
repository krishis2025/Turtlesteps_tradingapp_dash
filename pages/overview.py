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
            html.H3("Did Trade Come to you?", style={'textAlign': 'center', 'marginBottom': '0px'}),
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

        # NEW TILE 7: Grouped Bar Chart for Entry Quality Performance
        html.Div(id='entry-quality-bar-tile', style={
            'flex': '1 1 600px', # Wider tile for grouped bar chart
            'minHeight': '400px',
            'backgroundColor': '#ffffff',
            'borderRadius': '8px',
            'padding': '10px',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
        }, children=[
            html.H3("Performance by Entry Quality", style={'textAlign': 'center', 'marginBottom': '0px'}),
            dcc.Graph(id='entry-quality-bar-chart', config={'displayModeBar': False}, style={'height': '350px'})
        ]),
        
        # You can add more tiles here for other KPIs like Avg P&L per Trade, Avg Win/Loss Size, etc.
    ]),

    # Hidden interval for initial data load
    dcc.Interval(id='overview-interval', interval=1000, n_intervals=0, max_intervals=1),
])

# pages/overview.py - Add this callback at the end of the file
# Locate this section in pages/overview.py:
# @dash.callback(
#     Output('total-pnl-value', 'children'),
#     Output('win-rate-value', 'children'),
#     Output('total-trades-value', 'children'),
#     Output('avg-win-value', 'children'),
#     Output('avg-loss-value', 'children'),
#     Output('trade-came-pie-chart', 'figure'),
#     Output('emotional-state-pie-chart', 'figure'),
#     Input('overview-interval', 'n_intervals'),
#     prevent_initial_call=False
# )
# def update_overview_kpis(n_intervals):
#     ...

# REPLACE its entire content with this:
@dash.callback(
    Output('total-pnl-value', 'children'),
    Output('win-rate-value', 'children'),
    Output('total-trades-value', 'children'), # Average Trades per Day
    Output('avg-win-value', 'children'),
    Output('avg-loss-value', 'children'),
    Output('trade-came-pie-chart', 'figure'),
    Output('emotional-state-pie-chart', 'figure'),
    Output('entry-quality-bar-chart', 'figure'), # NEW OUTPUT for grouped bar chart
    Input('overview-interval', 'n_intervals'),
    prevent_initial_call=False
)
def update_overview_kpis(n_intervals):
    if n_intervals == 0: # This callback will run once on page load
        try:
            db.initialize_db() # Ensure DB is initialized before fetching
            all_trades = db.fetch_all_trades_from_db() # Fetch all historical data
        except Exception as e:
            print(f"Error fetching all historical trades for overview KPIs: {e}")
            # Return error state for all outputs
            return "$ N/A", "N/A%", "N/A", "$ N/A", "$ N/A", go.Figure(), go.Figure(), go.Figure()

        if not all_trades:
            return "$0.00", "0.00%", "0.00", "$0.00", "$0.00", go.Figure(), go.Figure(), go.Figure()

        df = pd.DataFrame(all_trades)
        df['Entry Time'] = pd.to_datetime(df['Entry Time'], errors='coerce')
        # Ensure valid data for calculations and pie charts, dropna early
        df = df.dropna(subset=['Entry Time', 'Realized P&L', 'Trade came to me', 'Emotional State', 'Entry Quality']) # Added Entry Quality to dropna

        # FIX: Robust Realized P&L conversion right here
        df['Realized P&L'] = pd.to_numeric(df['Realized P&L'], errors='coerce').fillna(0).astype(float)

        # If df becomes empty after cleaning (e.g., all relevant columns are NaN)
        if df.empty:
            print("DEBUG Overview: DataFrame is empty after cleaning. Returning empty charts.")
            return "$0.00", "0.00%", "0.00", "$0.00", "$0.00", go.Figure(), go.Figure(), go.Figure()

        # --- Call Helper Functions ---
        total_realized_pnl, win_rate, avg_trades_per_day, avg_win_size, avg_loss_size = _calculate_general_kpis(df)
        trade_origination_pie_fig = _create_trade_origination_pie_chart(df)
        emotional_state_pie_fig = _create_emotional_state_pie_chart(df)
        entry_quality_performance_fig = _create_entry_quality_bar_chart(df) # Call the new function


        # Return all calculated KPIs and figures
        return (
            f"${total_realized_pnl:,.2f}",
            f"{win_rate:,.2f}%",
            f"{avg_trades_per_day:,.2f}",
            f"${avg_win_size:,.2f}",
            f"${abs(avg_loss_size):,.2f}", # Display average loss as positive
            trade_origination_pie_fig,
            emotional_state_pie_fig,
            entry_quality_performance_fig # Ensure this is returned
        )
    return (
        dash.no_update, dash.no_update, dash.no_update, # P&L, Win Rate, Avg Trades
        dash.no_update, dash.no_update, # Avg Win/Loss
        dash.no_update, dash.no_update, # Pie charts
        dash.no_update # For the new grouped bar chart
    )

############################################################################
# Helper Functions
############################################################################
# pages/overview.py - Add these helper functions at the end of the file

def _calculate_general_kpis(df):
    """Calculates general KPIs (P&L, Win Rate, Avg Trades, Avg Win/Loss)."""
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
    
    return total_realized_pnl, win_rate, avg_trades_per_day, avg_win_size, avg_loss_size


def _create_trade_origination_pie_chart(df):
    """Creates the 'Did Trade Come To You' pie chart figure."""
    trade_origination_value_counts_series = df['Trade came to me'].value_counts(dropna=False)
    
    if trade_origination_value_counts_series.empty:
        print("DEBUG Overview: No data for 'Trade came to me' pie chart after value_counts.")
        return go.Figure().update_layout(title="No Trade Origination Data")
    else:
        trade_origination_counts = trade_origination_value_counts_series.reset_index()
        trade_origination_counts.columns = ['Category', 'Count']
        trade_origination_counts['Category'] = trade_origination_counts['Category'].fillna('Blank').replace('', 'Blank')
        
        origination_color_map = {
            'Yes': '#4CAF50', 'No': '#F44336', 'Blank': '#9E9E9E'
        }
        pie_colors_origination = [origination_color_map.get(cat, '#CCCCCC') for cat in trade_origination_counts['Category']]

        fig = go.Figure(data=[go.Pie(
            labels=trade_origination_counts['Category'],
            values=trade_origination_counts['Count'],
            hole=0.3,
            marker_colors=pie_colors_origination,
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )])
        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            showlegend=True,
            font={'color': '#333333'},
            paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
            height=250
        )
        return fig

#############################################################################
# def _create_emotional_state_pie_chart(df):
#############################################################################
def _create_emotional_state_pie_chart(df):
    """Creates the 'Emotional State' pie chart figure."""
    emotional_state_value_counts_series = df['Emotional State'].value_counts(dropna=False)
    
    if emotional_state_value_counts_series.empty:
        print("DEBUG Overview: No data for 'Emotional State' pie chart after value_counts.")
        return go.Figure().update_layout(title="No Emotional State Data")
    else:
        emotional_state_counts = emotional_state_value_counts_series.reset_index()
        emotional_state_counts.columns = ['Category', 'Count']
        emotional_state_counts['Category'] = emotional_state_counts['Category'].fillna('Blank').replace('', 'Blank')

        emotional_state_color_map = {
            'Calm': '#4CAF50', 
            'Fear of Loss': '#F44336', 
            'Fear of giving away profit': '#FF9800', 
            'Greed': '#FFEB3B', 
            'Overconfidence': '#9C27B0', 
            'Frustration / Impatience': '#FF5722', 
            'Distracted': '#607D8B', 
            'Blank': '#9E9E9E'
        }
        pie_colors_emotional_state = [emotional_state_color_map.get(cat, '#CCCCCC') for cat in emotional_state_counts['Category']]

        fig = go.Figure(data=[go.Pie(
            labels=emotional_state_counts['Category'],
            values=emotional_state_counts['Count'],
            hole=0.3,
            marker_colors=pie_colors_emotional_state,
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )])
        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            showlegend=True,
            font={'color': '#333333'},
            paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
            height=250
        )
        return fig


#############################################################################
# def _create_entry_quality_bar_chart(df):
#     """Creates the grouped bar chart for Performance by Entry Quality."""
#############################################################################
def _create_entry_quality_bar_chart(df):
    """Creates the grouped bar chart for Performance by Entry Quality."""
    entry_quality_performance_fig = go.Figure()
    
    df_entry_quality = df[df['Entry Quality'].notna() & (df['Entry Quality'] != '')].copy()

    if df_entry_quality.empty:
        entry_quality_performance_fig.update_layout(title="No Entry Quality Data")
    else:
        # FIX: Robust Realized P&L conversion for this helper function as well
        df_entry_quality['Realized P&L'] = pd.to_numeric(df_entry_quality['Realized P&L'], errors='coerce').fillna(0).astype(float)
        
        df_entry_quality['Is_Win'] = df_entry_quality['Realized P&L'] > 0

        performance_by_entry_quality = df_entry_quality.groupby('Entry Quality').agg(
            Total_P_L=('Realized P&L', 'sum'),
            Trade_Count=('Trade #', 'count'),
            Win_Count=('Is_Win', 'sum')
        ).reset_index()

        performance_by_entry_quality['Avg_P_L'] = performance_by_entry_quality['Total_P_L'] / performance_by_entry_quality['Trade_Count']
        performance_by_entry_quality['Win_Percentage'] = (performance_by_entry_quality['Win_Count'] / performance_by_entry_quality['Trade_Count']) * 100

        performance_by_entry_quality = performance_by_entry_quality.sort_values(by='Avg_P_L', ascending=False)

        # Add bars for Win %
        entry_quality_performance_fig.add_trace(go.Bar(
            x=performance_by_entry_quality['Entry Quality'],
            y=performance_by_entry_quality['Win_Percentage'],
            name='Win %',
            marker_color='#3498db', # Blue for Win %
            # NEW: Text inside bars for Win %
            text=performance_by_entry_quality['Win_Percentage'],
            texttemplate="%{y:,.2f}%", # Format as percentage
            textposition='outside', # Position text outside the bar
            # textposition='inside', # Position text inside the bar
            # insidetextanchor='middle', # Center text inside the bar
            insidetextfont={'color': 'white'}, # White text for contrast
            hovertemplate='<b>Entry Quality:</b> %{x}<br><b>Win %:</b> %{y:,.2f}%<extra></extra>'
        ))

        # Add bars for Avg P&L
        entry_quality_performance_fig.add_trace(go.Bar(
            x=performance_by_entry_quality['Entry Quality'],
            y=performance_by_entry_quality['Avg_P_L'],
            name='Avg P&L',
            marker_color='#2ecc71', # Green for Avg P&L
            # NEW: Text inside bars for Avg P&L
            text=performance_by_entry_quality['Avg_P_L'],
            texttemplate="$%{y:,.2f}", # Format as currency
            textposition='outside', # Position text outside the bar
            #textposition='inside', # Position text inside the bar            
            #insidetextanchor='middle', # Center text inside the bar
            insidetextfont={'color': 'white'}, # White text for contrast
            hovertemplate='<b>Entry Quality:</b> %{x}<br><b>Avg P&L:</b> $%{y:,.2f}<extra></extra>'
        ))
        
        entry_quality_performance_fig.update_layout(
            barmode='group', # Group bars side by side
            title='Performance by Entry Quality',
            xaxis_title='Entry Quality Tag',
            yaxis_title='Value', # Y-axis will show both % and $
            yaxis={'side': 'left', 'title': 'Win %'}, # Primary Y-axis for Win %
            yaxis2={'side': 'right', 'overlaying': 'y', 'title': 'Avg P&L ($)'}, # Secondary Y-axis for Avg P&L
            margin=dict(t=40, b=40, l=40, r=40),
            paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
            font={'color': '#333333'},
            height=350,
            legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.7)', bordercolor='rgba(0,0,0,0.1)'),
        )
    return entry_quality_performance_fig