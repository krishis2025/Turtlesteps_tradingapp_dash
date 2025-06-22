import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date, timedelta # Added timedelta for date calculations

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
    print(f"Error: {CONFIG_FILE} not found for pages/calendar_view.py. Using default settings.")
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
    path='/calendar',
    name='Calendar View',
    title='Trading Dashboard - Calendar',
    description='Calendar visualization of daily trade performance.'
)

# --- Layout for the Calendar View Page ---
layout = html.Div([
    html.H2("Daily Performance Calendar", style={'textAlign': 'center', 'marginBottom': '20px'}),

    # Navigation Controls (Month/Year)
    html.Div([
        html.Button("<< Prev Year", id="prev-year-button", className="dash-button", style={'marginRight': '10px'}),
        html.Button("< Prev Month", id="prev-month-button", className="dash-button", style={'marginRight': '20px'}),
        html.H3(id="current-month-year-display", style={'margin': '0 20px', 'minWidth': '150px', 'textAlign': 'center'}),
        html.Button("Next Month >", id="next-month-button", className="dash-button", style={'marginLeft': '20px'}),
        html.Button("Next Year >>", id="next-year-button", className="dash-button", style={'marginLeft': '10px'}),
    ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '30px'}),

    # Calendar Grid Container
    html.Div(id='calendar-grid-container', style={
        'display': 'grid',
        'grid-template-columns': 'repeat(7, 1fr)', # 7 columns for days of week
        'gap': '5px', # Gap between cells
        'width': '95%',
        'maxWidth': '1000px', # Max width for the whole calendar
        'margin': '0 auto', # Center the calendar
        'padding': '15px',
        'backgroundColor': '#ffffff',
        'borderRadius': '8px',
        'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)'
    }, children=[
        # Weekday Headers (Mon, Tue, etc.)
        html.Div("Mon", style={'textAlign': 'center', 'fontWeight': 'bold', 'padding': '10px', 'backgroundColor': '#e9eef2', 'borderRadius': '4px'}),
        html.Div("Tue", style={'textAlign': 'center', 'fontWeight': 'bold', 'padding': '10px', 'backgroundColor': '#e9eef2', 'borderRadius': '4px'}),
        html.Div("Wed", style={'textAlign': 'center', 'fontWeight': 'bold', 'padding': '10px', 'backgroundColor': '#e9eef2', 'borderRadius': '4px'}),
        html.Div("Thu", style={'textAlign': 'center', 'fontWeight': 'bold', 'padding': '10px', 'backgroundColor': '#e9eef2', 'borderRadius': '4px'}),
        html.Div("Fri", style={'textAlign': 'center', 'fontWeight': 'bold', 'padding': '10px', 'backgroundColor': '#e9eef2', 'borderRadius': '4px'}),
        html.Div("Sat", style={'textAlign': 'center', 'fontWeight': 'bold', 'padding': '10px', 'backgroundColor': '#e9eef2', 'borderRadius': '4px'}),
        html.Div("Sun", style={'textAlign': 'center', 'fontWeight': 'bold', 'padding': '10px', 'backgroundColor': '#e9eef2', 'borderRadius': '4px'}),
        # Day cells will be populated by callback
    ]),

    # Hidden Store to keep track of current displayed month/year
    dcc.Store(id='current-calendar-date', data={'year': datetime.now().year, 'month': datetime.now().month}),
    # Hidden interval for initial data load
    dcc.Interval(id='calendar-interval', interval=1000, n_intervals=0, max_intervals=1), # Triggers once after 1 second
])


# --- Callbacks for the Calendar View Page ---

@dash.callback(
    Output('calendar-grid-container', 'children'),
    Output('current-month-year-display', 'children'),
    Output('current-calendar-date', 'data'), # Store updated month/year
    Input('prev-month-button', 'n_clicks'),
    Input('next-month-button', 'n_clicks'),
    Input('prev-year-button', 'n_clicks'),
    Input('next-year-button', 'n_clicks'),
    Input('calendar-interval', 'n_intervals'), # Initial load trigger
    State('current-calendar-date', 'data')
)
def update_calendar_view(prev_month_clicks, next_month_clicks, prev_year_clicks, next_year_clicks, n_intervals, current_calendar_data):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'initial_load'

    # Retrieve current year and month from the dcc.Store
    current_year = current_calendar_data['year']
    current_month = current_calendar_data['month']

    # Adjust month/year based on button clicks
    if trigger_id == 'prev-month-button':
        current_month -= 1
        if current_month < 1:
            current_month = 12
            current_year -= 1
    elif trigger_id == 'next-month-button':
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
    elif trigger_id == 'prev-year-button':
        current_year -= 1
    elif trigger_id == 'next-year-button':
        current_year += 1
    elif trigger_id == 'initial_load':
        pass # Use default current_year, current_month from dcc.Store initialization

    # Get the first day of the current month
    first_day_of_month = date(current_year, current_month, 1)
    # Calculate which day of the week the first day is (Monday=0, Sunday=6)
    first_weekday = first_day_of_month.weekday()

    # Calculate number of days in the current month
    if current_month == 12:
        days_in_month = (date(current_year + 1, 1, 1) - first_day_of_month).days
    else:
        days_in_month = (date(current_year, current_month + 1, 1) - first_day_of_month).days

    # Fetch all historical data for aggregation
    try:
        db.initialize_db()
        all_trades = db.fetch_all_trades_from_db()
    except Exception as e:
        print(f"Error fetching all historical trades for calendar: {e}")
        # Ensure month/year display is still correct even on error
        return html.Div("Error loading trades for calendar.", style={'textAlign': 'center', 'color': 'red'}), \
               f"{first_day_of_month.strftime('%B %Y')}", \
               {'year': current_year, 'month': current_month} # Return updated store state

    df = pd.DataFrame(all_trades)
    df['Entry Time'] = pd.to_datetime(df['Entry Time'], errors='coerce')
    df = df.dropna(subset=['Entry Time', 'Realized P&L'])
    df['Date'] = df['Entry Time'].dt.date # Extract just the date
    df['Realized P&L'] = pd.to_numeric(df['Realized P&L'], errors='coerce').fillna(0).astype(float)

    # Filter trades for the current displayed month/year
    df_current_month = df[(df['Entry Time'].dt.year == current_year) & (df['Entry Time'].dt.month == current_month)]

    daily_summary = df_current_month.groupby('Date').agg(
        Total_P_L=('Realized P&L', 'sum'),
        Trade_Count=('Trade #', 'count')
    ).reset_index()

    # Build calendar cells
    calendar_cells = []
    # Add weekday Headers (already in layout, but need to reconstruct children to match grid)
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for day_name in weekdays:
        calendar_cells.append(html.Div(day_name, style={'textAlign': 'center', 'fontWeight': 'bold', 'padding': '10px', 'backgroundColor': '#e9eef2', 'borderRadius': '4px'}))

    # Add empty cells for days before the 1st of the month
    for _ in range(first_weekday): # weekday() returns 0 for Monday, so if first day is Wed (2), we need 2 empty cells
        calendar_cells.append(html.Div(style={'backgroundColor': '#f8f8f8', 'borderRadius': '4px', 'minHeight': '100px'})) # Added minHeight for empty cells

    # Populate actual day cells
    for day_num in range(1, days_in_month + 1):
        current_date_obj = date(current_year, current_month, day_num)
        day_summary = daily_summary[daily_summary['Date'] == current_date_obj]

        total_p_l = 0
        trade_count = 0
        
        if not day_summary.empty:
            total_p_l = day_summary['Total_P_L'].iloc[0]
            trade_count = day_summary['Trade_Count'].iloc[0]
        
        # Determine cell background color based on P&L
        cell_bgcolor = '#ffffff' # Default for no trades or break-even
        cell_text_color = '#333333' # Default text color
        if total_p_l > 0:
            cell_bgcolor = '#E8F5E9' # Light green for profit
            cell_text_color = '#1B5E20' # Dark green text
        elif total_p_l < 0:
            cell_bgcolor = '#FFEBEE' # Light red for loss
            cell_text_color = '#CC0000' # Dark red text

        # Format P&L for display
        p_l_display = f"${total_p_l:,.2f}" if total_p_l != 0 else ""
        trades_display = f"{trade_count} trade" if trade_count == 1 else f"{trade_count} trades"
        if trade_count == 0:
            trades_display = "No Trades"
            p_l_display = "" # Don't show $0.00 if no trades

        cell_children = [
            html.Div(str(day_num), style={'fontWeight': 'bold', 'textAlign': 'right', 'paddingRight': '5px'}),
            html.Div(p_l_display, style={'fontSize': '0.9em', 'textAlign': 'right', 'paddingRight': '5px', 'color': cell_text_color}),
            html.Div(trades_display, style={'fontSize': '0.7em', 'textAlign': 'right', 'paddingRight': '5px', 'color': cell_text_color})
        ]

        calendar_cells.append(
            html.Div(
                children=cell_children,
                style={
                    'backgroundColor': cell_bgcolor,
                    'borderRadius': '4px',
                    'padding': '5px',
                    'height': '100px', # Fixed height for cells
                    'display': 'flex',
                    'flexDirection': 'column',
                    'justifyContent': 'flex-start',
                    'alignItems': 'flex-end', # Align content to top-right
                    'border': '1px solid #e0e0e0', # Subtle border for cells
                    'boxSizing': 'border-box'
                }
            )
        )
    
    # Store updated month/year for next callback run
    updated_calendar_data = {'year': current_year, 'month': current_month}

    return calendar_cells, f"{first_day_of_month.strftime('%B %Y')}", updated_calendar_data