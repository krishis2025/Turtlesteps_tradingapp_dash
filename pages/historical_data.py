# pages/historical_data.py

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import pandas as pd
import sys
import os

# Add 'utils' to Python path so you can import 'database'
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
import database as db # Import your database utility functions

# --- Page Registration ---
dash.register_page(
    __name__,
    path='/history',  # URL path for the historical data page
    name='Historical Data', # Name for navigation link
    title='Trading Dashboard - History',
    description='View and manage all historical trade data.'
)

# --- Layout for the Historical Data Page ---
layout = html.Div([
    html.H2("All Historical Trades", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    html.Div([
        html.Button("Load All Trades from Database", id="load-all-trades-button", n_clicks=0,
                    style={'marginBottom': '10px', 'padding': '10px 20px', 'fontSize': '16px', 'cursor': 'pointer'}),
        html.Div(id='load-db-output-message', style={'marginTop': '10px', 'textAlign': 'center'}) # Message area
    ], style={'textAlign': 'left', 'marginBottom': '20px'}), # Left-aligned button

    # DataTable to display historical data
    html.Div([
        dash_table.DataTable(
            id='historical-trades-table', # Unique ID for this table
            columns=[
                {"name": "Trade #", "id": "Trade #", "type": "numeric", "editable": False},
                {"name": "Futures Type", "id": "Futures Type", "presentation": "dropdown"},
                {"name": "Size", "id": "Size", "type": "numeric", "editable": True},
                {"name": "Stop Loss (pts)", "id": "Stop Loss (pts)", "type": "numeric", "editable": True},
                {"name": "Risk ($)", "id": "Risk ($)", "type": "numeric", "editable": False},
                {"name": "Status", "id": "Status", "presentation": "dropdown"},
                {"name": "Points Realized", "id": "Points Realized", "type": "numeric", "editable": True},
                {"name": "Realized P&L", "id": "Realized P&L", "type": "numeric", "editable": False, "format": {"specifier": ".2f"}},
                {"name": "Entry Time", "id": "Entry Time", "editable": False},
                {"name": "Exit Time", "id": "Exit Time", "editable": True},
                {"name": "Trade came to me", "id": "Trade came to me", "presentation": "dropdown"},
                {"name": "With Value", "id": "With Value", "presentation": "dropdown"},
                {"name": "Score", "id": "Score", "presentation": "dropdown"},
                {"name": "Entry Quality", "id": "Entry Quality", "presentation": "dropdown"},
                {"name": "Emotional State", "id": "Emotional State", "presentation": "dropdown"},
                {"name": "Sizing", "id": "Sizing", "presentation": "dropdown"},
                {"name": "Notes", "id": "Notes", "type": "text", "editable": True},
            ],
            data=[], # Starts empty, data loaded by callback
            editable=True, # Will allow editing/deleting historical trades directly
            row_deletable=True,
            # Add filtering and pagination later if needed for this table
            page_action="native", # Enable pagination
            page_size=20, # Number of rows per page
            sort_action="native", # Enable sorting
            filter_action="native", # Enable filtering
            style_table={'overflowX': 'auto'} # Allow table to scroll horizontally if needed
        )
    ], style={'width': '95%', 'margin': '0 auto'})
])

# --- Callbacks for the Historical Data Page ---

@dash.callback(
    Output('historical-trades-table', 'data'),
    Output('load-db-output-message', 'children'),
    Input('load-all-trades-button', 'n_clicks'),
    prevent_initial_call=True
)
def load_all_trades_into_table(n_clicks):
    if n_clicks > 0:
        try:
            db.initialize_db() # Ensure DB is initialized before fetching
            all_trades = db.fetch_all_trades_from_db()
            message = f"Loaded {len(all_trades)} trades from database."
            return all_trades, html.Div(message, style={'color': 'green'})
        except Exception as e:
            message = f"Error loading trades from database: {e}"
            return [], html.Div(message, style={'color': 'red'})
    return dash.no_update, ""