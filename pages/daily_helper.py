import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table, callback_context
import json
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import io # For dcc.send_data_frame
import base64 # Needed for load_trades_json

# ADD THESE LINES SQLlite integration
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils')) # Add 'utils' to Python path
import database as db # Import your database utility functions


# Load config (assuming config.json is in the project root)
CONFIG_FILE = 'config.json'
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Error: {CONFIG_FILE} not found. Please create it with the specified structure.")
    # Provide a default minimal config to prevent app crash if file is missing during development
    config = {
        "daily_risk": 550,
        "profit_target": 600,
        "max_trades_per_day": 6,
        "default_futures_type": "MES",
        "default_size": 5,
        "futures_types": {"ES": { "mf": 50 }, "MES": { "mf": 5 }}
    }

# Initialize the database when this page module is imported
# This ensures the DB file and table are created/ready
try:
    db.initialize_db()
except Exception as e:
    print(f"Error initializing database from daily_helper.py: {e}")
    # You might want a more visible error on the dashboard if DB init fails.

# Register this page with Dash
dash.register_page(
    __name__,
    path='/',  # This makes 'daily_helper.py' the default page at the root URL
    name='Daily Helper', # Name that will appear in navigation links
    title='Trading Dashboard - Daily Helper',
    description='Daily trade entry and monitoring.'
)


# Load today's trades from the database for initial display
initial_data = []
try:
    # Fetch trades for today's date from DB
    today_date = datetime.now().date()
    initial_data = db.fetch_trades_by_date(today_date)
    db_name, table_name = db.get_database_info()
    print(f"Loaded {len(initial_data)} trades for {today_date} from DB '{db_name}' table '{table_name}'.")
except Exception as e:
    print(f"Error loading today's data from DB for daily helper: {e}")
    # Initial data remains empty if there's an error

# --- Layout for the Daily Helper Page ---
layout = html.Div(style={'width': '100%', 'boxSizing': 'border-box'}, children=[
    html.Div([
        html.H2("Daily Trade Log", className="page-title")
    ], style={'display': 'flex', 'justifyContent': 'center', 'width': '100%'}),
    #html.H2("Daily Logger", className="page-title"), #style={'textAlign': 'center', 'marginBottom': '0px'}),


    # Main Dashboard Content (pulled out from Home tab, now directly in app.layout)    
    html.Div(id="home-tab-content-wrapper", style={'minHeight': '800px', 'padding': '0px', 'backgroundColor': 'transparent', 'width': '100%'}, children=[
        # NEW: Date Picker for daily metrics
        html.Div([
            html.Label("View Data For:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.DatePickerSingle(
                id='date-picker-single',
                month_format='MMMM Y',
                placeholder='Select a date',
                date=datetime.now().date(), # Default to today's date
                display_format='MM-DD-YYYY', # CHANGED: Date format
                style={'width': '150px'} # ADDED: Style to make it smaller
            ),
        ], style={'textAlign': 'right', 'marginBottom': '15px'}), # CHANGED: textAlign to 'left'
        # Main container for the two-column indicator section
        html.Div([
            # Column 1: Available Risk Gauge
            html.Div([
                #html.H3("Available Risk", className="gauge-title"),
                dcc.Graph(id='available-risk-gauge', config={'displayModeBar': False},
                          style={'height': '180px', 'width': '100%', 'backgroundColor': 'transparent'}), 
            ], style={'flex': '1 1 350px', 'paddingRight': '10px', 'boxSizing': 'border-box', 'justifyContent': 'center'}), # Changed flex-basis to 350px, added boxSizing

            # Column 2: Stacked Progress Bars and Placeholder
            html.Div([
                # Row 1: Realized P&L Progress Bar
                html.Div([
                    html.H3("Realized P&L Progress", className="gauge-title"), #style={'textAlign': 'center'}),
                    html.Div(id='pnl-progress-bar-container', style={'width': '100%', 'height': 'auto'}),
                ], style={'width': '100%', 'height': 'auto', 'maxWidth': '100%', 'boxSizing': 'border-box', 'marginBottom': '25px', 'margintop': '100px'}), # Added maxWidth: '100%', boxSizing

                # Row 2: Trades per Day Progress Bar
                html.Div([
                    html.H3("Trades per Day", className="gauge-title"), #style={'textAlign': 'center'}),
                    html.Div(id='trades-progress-bar-container', style={'width': '100%', 'height': 'auto'}),
                ], style={'width': '100%', 'height': 'auto', 'maxWidth': '100%', 'boxSizing': 'border-box', 'marginBottom': '30px'}), # Added maxWidth: '100%', boxSizing

                # Row 3: Pressing Roadmap
                html.Div([
                    html.Div(
                        id="pressing-roadmap-hover-target",
                        style={
                            'width': '100%',
                            'minHeight': '20px',
                            'textAlign': 'center',
                            'marginTop': '0',
                            'marginBottom': '5px',
                            'cursor': 'help',
                            'position': 'relative'
                        },
                        children=[
                            html.P(
                                "This roadmap shows your current pressing level based on consecutive wins. Win: advance. Loss/Break-even: reset to 1x.",
                                className="roadmap-explanation-text",
                                style={
                                    'fontSize': '12px',
                                    'textAlign': 'center',
                                    'margin': '0',
                                    'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                                    'color': 'white',
                                    'padding': '5px 10px',
                                    'borderRadius': '5px',
                                    'whiteSpace': 'nowrap',
                                    'position': 'absolute',
                                    'bottom': '100%',
                                    'left': '50%',
                                    'transform': 'translateX(-50%)',
                                    'zIndex': '10',
                                    'opacity': '0',
                                    'visibility': 'hidden',
                                    'transition': 'opacity 0.3s ease-in-out, visibility 0.3s ease-in-out'
                                }
                            )
                        ]
                    ),
                    html.Div(id='pressing-roadmap-container', style={'width': '100%', 'height': 'auto', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexWrap': 'wrap', 'padding': '10px 0'}),
                ], style={'width': '100%', 'height': 'auto', 'maxWidth': '100%', 'boxSizing': 'border-box', 'marginBottom': '0px'}), # Added maxWidth: '100%', boxSizing

            ], style={'flex': '1 1 350px', 'paddingLeft': '10px', 'boxSizing': 'border-box', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-around'}),
        ], style={
            'display': 'flex',
            'flexWrap': 'wrap', # CRUCIAL: Confirmed to be here
            'justifyContent': 'space-around',
            'alignItems': 'flex-start',
            'width': '100%',
            'marginBottom': '20px',
            'padding': '20px',
            'boxSizing': 'border-box' # Ensures padding/border are included in the width
        }),

        # Export to Excel Button
        html.Div([
            html.Button("Export to Excel", id="export-excel-button", n_clicks=0,
                        className='dash-button', style={'marginBottom': '10px'}),
        ], style={'width': '95%', 'margin': '0 auto 20px auto', 'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap', 'justifyContent': 'flex-start', 'padding': '0 20px'}),

        # DataTable
        html.Div([
            dash_table.DataTable(
                id='trades-table',
                columns=[
                    # Define the columns for the DataTable
                    {"name": "DB ID", "id": "id", "type": "numeric", "editable": False, "hideable": True}, # CORRECTED: Removed 'header_align'
                    {"name": "Trade #", "id": "Trade #", "type": "numeric", "editable": False},
                    {"name": "Futures Type", "id": "Futures Type", "presentation": "dropdown"},
                    {"name": "Size", "id": "Size", "type": "numeric", "editable": True},
                    {"name": "Stop Loss (pts)", "id": "Stop Loss (pts)", "type": "numeric", "editable": True},
                    {"name": "Risk ($)", "id": "Risk ($)", "type": "numeric", "editable": False},
                    {"name": "Status", "id": "Status"}, #"presentation": "dropdown"},
                    {"name": "Points Realized", "id": "Points Realized", "type": "numeric", "editable": True},
                    {"name": "Realized P&L", "id": "Realized P&L", "type": "numeric", "editable": False, "format": {"specifier": ".2f"}},
                    {"name": "Entry Time", "id": "Entry Time", "editable": False},
                    {"name": "Exit Time", "id": "Exit Time", "editable": True},
                    {"name": "Trade came to me", "id": "Trade came to me"}, # "presentation": "dropdown"},
                    {"name": "With Value", "id": "With Value"}, #, "presentation": "dropdown"},
                    {"name": "Market Conditions", "id": "Market Conditions", "presentation": "dropdown", "editable": True, "hideable": True}, # NEW COLUMN
                    {"name": "Score", "id": "Score"}, #, "presentation": "dropdown"},
                    {"name": "Entry Quality", "id": "Entry Quality"}, #, "presentation": "dropdown"},
                    {"name": "Emotional State", "id": "Emotional State", "presentation": "dropdown", "hideable": True},
                    {"name": "Sizing", "id": "Sizing", "presentation": "dropdown"},
                    {"name": "Notes", "id": "Notes", "type": "text", "editable": True},
                ],
                data=initial_data,
                editable=True,
                row_deletable=True,
                style_table={
                    'overflowX': 'auto', # Allows horizontal scrolling within the table if content overflows
                    'minWidth': '100%',  # Ensures the table tries to take full width available
                },
                dropdown={
                    'Futures Type': {
                        'options': [{'label': i, 'value': i} for i in config['futures_types'].keys()],
                        'clearable': False
                    },
                    'Status': {
                        'options': [{'label': i, 'value': i} for i in ['Active', 'Win', 'Loss']],
                        'clearable': False
                    },
                    'Trade came to me': {
                        'options': [{'label': 'Yes', 'value': 'Yes'}, {'label': 'No', 'value': 'No'}, {'label': ' ', 'value': ''}],
                        'clearable': False
                    },
                    'With Value': {
                        'options': [{'label': 'Yes', 'value': 'Yes'}, {'label': 'No', 'value': 'No'}, {'label': ' ', 'value': ''}],
                        'clearable': False
                    },
                    'Score': {
                        'options': [
                            {'label': ' ', 'value': ''},
                            {'label': 'A+', 'value': 'A+'},
                            {'label': 'B', 'value': 'B'},
                            {'label': 'C', 'value': 'C'},
                        ],
                        'clearable': False
                    },
                    'Entry Quality': {
                        'options': [
                            {'label': ' ', 'value': ''},                            
                            {'label': 'Calm / Waited Patiently', 'value': 'Calm / Waited Patiently'},
                            {'label': 'Impulsive / FOMO', 'value': 'Impulsive / FOMO'},                                
                            {'label': 'Forced / Overtraded', 'value': 'Forced / Overtraded'},
                            {'label': 'Get back losses', 'value': 'Get back losses'},
                            {'label': 'Hesitant / Missed', 'value': 'Hesitant / Missed'},
                        ],
                        'clearable': False
                    },
                    'Emotional State': {
                        'options': [
                            {'label': ' ', 'value': ''},
                            {'label': 'Calm', 'value': 'Calm'},
                            {'label': 'Fear of Loss', 'value': 'Fear of Loss'},                            
                            {'label': 'Fear of giving away profit', 'value': 'Fear of giving away profit'},
                            {'label': 'Greed', 'value': 'Greed'},
                            {'label': 'Overconfidence', 'value': 'Overconfidence'},
                            {'label': 'Frustration / Impatience', 'value': 'Frustration / Impatience'},
                            {'label': 'Distracted', 'value': 'Distracted'},
                        ],
                        'clearable': False
                    },
                    'Sizing': {
                        'options': [{'label': i, 'value': i} for i in ['Base', 'Press', 'derisk']],
                        'clearable': False
                    },
                },              
                style_data_conditional=[
                    # Existing Conditional styling for Risk ($) exceeding daily_risk (applies to whole row)
                    { # NEW: Center content in 'Status' column
                        'if': {'column_id': 'Status'},
                        'textAlign': 'center'
                    },
                    { # NEW: Color ONLY 'Risk ($)' cell if risk is too high
                        'if': {
                            'column_id': 'Risk ($)', # Target only the 'Risk ($)' column
                            'filter_query': '{Risk ($)} > ' + str(config['daily_risk'])
                        },
                        'backgroundColor': '#CC0000', # Darker red for emphasis
                        'color': 'white' # White text for contrast on dark red
                    },
                    # NEW: Cell-specific coloring for 'Status' column based on its text content
                    {
                        'if': {
                            'column_id': 'Status', # Target only the Status column
                            'filter_query': '{Status} = "Win"' # Condition for Win
                        },
                        'backgroundColor': '#E8F5E9', # Very light green for profit (subtler)
                        'color': '#1B5E20' # Dark green text for contrast
                    },
                    {
                        'if': {
                            'column_id': 'Status', # Target only the Status column
                            'filter_query': '{Status} = "Loss"' # Condition for Lose
                        },
                        'backgroundColor': '#FFEBEE', # Very light red for loss (subtler)
                        'color': '#CC0000' # Dark red text for contrast
                    },
                    {
                        'if': {
                            'column_id': 'Status', # Target only the Status column
                            'filter_query': '{Status} = "BE" || {Status} = "Active"' # Condition for Break-Even or Active status
                        },
                        'backgroundColor': '#FFFDE7', # Very light yellow for break-even
                        'color': '#FF6F00' # Orange text
                    },                                    
                ],
                style_cell={
                    'textAlign': 'left', # Keep left alignment for text, center for numbers if needed
                    'padding': '7px 5px', # Reduced padding for sleek rows
                    'fontFamily': 'Arial, sans-serif',
                    'fontSize': '13px', # Consistent font size
                    'borderBottom': '1px solid #e0e0e0', # Lighter bottom border for horizontal lines
                    'borderLeft': 'none', # Remove vertical borders
                    'borderRight': 'none', # Remove vertical borders
                    'whiteSpace': 'nowrap', # CRUCIAL: Prevents cell content from wrapping (keeps it on one line)
                    'overflow': 'visible', # ALLOWS content to overflow if needed, for column expansion
                    'textOverflow': 'clip', # Prevents '...' from appearing, content will just clip or push column
                    'height': 'auto', # Allow row height to adjust
                    # min/width/maxWidth for columns are typically better managed in style_cell_conditional
                    'minWidth': '80px', 'width': 'auto', 'maxWidth': '300px' # Allow width to be auto/expand up to 300px
                },
                style_header={
                    'backgroundColor': '#f8f8f8', # Lighter header background
                    'color': '#2c3e50', # Darker header text
                    'fontWeight': 'bold',
                    'textAlign': 'left',
                    'fontSize': '14px', # Consistent font size
                    'padding': '8px 5px', # Reduced padding for sleek headers
                    'borderBottom': '2px solid #dde3e9',
                    'borderLeft': 'none',
                    'borderRight': 'none',
                    'whiteSpace': 'nowrap', # CRUCIAL: Prevents header content from wrapping
                    'overflow': 'visible', # ALLOWS header content to overflow if needed, for column expansion
                    'textOverflow': 'clip', # Prevents '...' from appearing
                },
                css=[{
                    'selector': '.dash-spreadsheet-container .dash-spreadsheet-table',
                    'rule': 'font-size: 14px;'
                },
                {
                    'selector': '.dash-cell div.dash-dropdown .Select-value-label',
                    'rule': 'padding-right: 25px !important;'
                },
                {
                    'selector': '.dash-cell div.dash-dropdown .Select-arrow',
                    'rule': 'right: 5px !important;'
                }
                ]
            )
        ], style={'marginTop': '20px', 'marginBottom': '20px', 'width': '100%', 'margin': '0 auto', 'overflowX': 'auto', 'padding': '0 20px'}), # Added horizontal padding

        # Section for Input Fields (below table)       
        html.Div([
            html.H3("New Trade Entry", style={'textAlign': 'center', 'marginTop': '20px', 'marginBottom': '15px'}),

            # Main container for the 3 columns
            html.Div([
                # Column 1
                html.Div([
                    #Row1: Did Trade Come to You?
                    html.Div([
                        html.Label("Did trade come to you?", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id='input-trade-came-to-you',
                            options=[{'label': 'Yes', 'value': 'Yes'}, {'label': 'No', 'value': 'No'}, {'label': ' ', 'value': ''}],
                            value='',
                            clearable=False,
                            style={'width': '100%'}
                        )
                    ], style={'marginBottom': '15px'}),
                    #Row2: With Value?
                    html.Div([
                        html.Label("With Value?", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id='input-with-value',
                            options=[{'label': 'Yes', 'value': 'Yes'}, {'label': 'No', 'value': 'No'}, {'label': ' ', 'value': ''}],
                            value='',
                            clearable=False,
                            style={'width': '100%'}
                        )
                    ], style={'marginBottom': '15px'}),

                    # NEW ROW: Market Conditions
                    html.Div([
                        html.Label("Market Conditions:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id='input-market-conditions', # NEW ID
                            options=[
                                {'label': 'Trending', 'value': 'Trending'},
                                {'label': 'Balancing/Range', 'value': 'Balancing/Range'},
                                {'label': ' ', 'value': ''} # Option for blank
                            ],
                            value='', # Default to blank
                            clearable=False,
                            style={'width': '100%'}
                        )
                    ], style={'marginBottom': '15px'}), # Consistent spacing

                ], style={'flex': '1 1 auto', 'padding': '0 10px', 'boxSizing': 'border-box', 'maxWidth': 'calc(33.33% - 20px)'}),

                # Column 2
                html.Div([
                    #Row1: Entry Quality
                    html.Div([
                        html.Label("Entry Quality:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                        dcc.Dropdown(
                            id='input-entry-quality',
                            options=[
                                {'label': ' ', 'value': ''},                                
                                {'label': 'Calm / Waited Patiently', 'value': 'Calm / Waited Patiently'},
                                {'label': 'Impulsive / FOMO', 'value': 'Impulsive / FOMO'},                                
                                {'label': 'Forced / Overtraded', 'value': 'Forced / Overtraded'},
                                {'label': 'Get back losses', 'value': 'Get back losses'},
                                {'label': 'Hesitant / Missed', 'value': 'Hesitant / Missed'},
                            ],
                            value='',
                            clearable=False,
                            style={'width': '100%'}
                        )
                    ], style={'marginBottom': '15px'}),
                    #Row2: Emotional State
                    html.Div([
                        html.Label("Emotional State:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                        dcc.Dropdown(
                            id='input-psychological-state',
                            options=[
                                {'label': ' ', 'value': ''},                                
                                {'label': 'Calm', 'value': 'Calm'},                                
                                {'label': 'Fear of Loss', 'value': 'Fear of Loss'},                            
                                {'label': 'Fear of giving away profit', 'value': 'Fear of giving away profit'},
                                {'label': 'Greed', 'value': 'Greed'},
                                {'label': 'Overconfidence', 'value': 'Overconfidence'},
                                {'label': 'Frustration / Impatience', 'value': 'Frustration / Impatience'},
                                {'label': 'Distracted', 'value': 'Distracted'},
                            ],
                            value='',                            
                            clearable=False, 
                            style={'width': '100%'}
                        )
                    ], style={'marginBottom': '15px'}),
                    #Row3: Score
                    html.Div([
                        html.Label("Score:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                        dcc.Dropdown(
                            id='input-score',
                            options=[
                                {'label': ' ', 'value': ''},
                                {'label': 'A+', 'value': 'A+'},
                                {'label': 'B', 'value': 'B'},
                                {'label': 'C', 'value': 'C'},
                            ],
                            value='',
                            clearable=False,
                            style={'width': '100%'}
                        )
                    ], style={'marginBottom': '0px'}),

                ], style={'flex': '1 1 auto', 'padding': '0 10px', 'boxSizing': 'border-box', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-between', 'maxWidth': 'calc(33.33% - 20px)'}),

                # Column 3 (Notes)
                html.Div([
                    html.Label("Notes (max 400 chars):", style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
                    dcc.Textarea(
                        id='input-notes',
                        placeholder='Enter notes here...',
                        maxLength=400,
                        value='',
                        style={'width': '100%', 'height': '180px', 'resize': 'vertical'}
                    )
                ], style={'flex': '1 1 auto', 'padding': '0 10px', 'boxSizing': 'border-box', 'display': 'flex', 'flexDirection': 'column', 'maxWidth': 'calc(33.33% - 20px)'}),

            ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'alignItems': 'flex-start', 'width': '100%', 'marginBottom': '20px', 'boxSizing': 'border-box'}),

        ], style={'border': '1px solid #ddd', 'borderRadius': '5px', 'padding': '20px', 'marginTop': '20px', 'marginBottom': '20px', 'boxSizing': 'border-box'}),
         

        # Add Trade button (Moved here, and is now the only one)
        html.Div([
            html.Button('Add Trade', id='add-trade-button', n_clicks=0, 
                        className='dash-button', style={'marginBottom': '20px'}),
        ], style={'textAlign': 'left', 'width': '100%', 'margin': '0 auto', 'padding': '20px'}), # Added horizontal padding
    ]), 

    # NEW: Main Tabs for Analytical Views (elevated from 'inner-analytical-tabs')
    dcc.Tabs(id="main-analytical-tabs", value='tab-cumulative-pnl', children=[ # ID changed to main-analytical-tabs
        dcc.Tab(label='Cumulative P&L', value='tab-cumulative-pnl', children=[
            html.Div([
                dcc.Graph(id='cumulative-pnl-chart', style={'height': '400px', 'width': '100%'}) # ADDED width: '100%'
            ], style={'padding': '20px'})
        ]),
        dcc.Tab(label='KPIs', value='tab-kpis', children=[
            html.Div([
                html.Div(id='kpis-content', style={'padding': '20px'})
            ], style={'padding': '20px'})
        ]),
        dcc.Tab(label='P&L Breakdown by Category', value='tab-pnl-breakdown', children=[
            html.Div([
                # SNIPPET FOR THE DROPDOWN FILTER HERE
                html.Label("Draw PnL by Category:", style={'fontWeight': 'bold', 'marginRight': '10px', 'display': 'block', 'textAlign': 'center'}),
                dcc.Dropdown(
                    id='pnl-breakdown-category-filter',
                    options=[
                        {'label': 'Entry Quality', 'value': 'Entry Quality'},
                        {'label': 'Emotional State', 'value': 'Emotional State'},
                        {'label': 'Score', 'value': 'Score'},
                        {'label': 'Trade came to you', 'value': 'Trade came to me'}, # NEW OPTION
                        {'label': 'With Value', 'value': 'With Value'},               # NEW OPTION
                        {'label': 'Show All', 'value': 'Show All'}
                    ],
                    value='Show All',
                    clearable=False,
                    style={'width': '50%', 'margin': '10px auto 20px auto'}
                ),
                html.Div(id='breakdown-content', style={'padding': '20px'})
            ], style={'padding': '20px'})
        ]),
    ]), # End of main-analytical-tabs
    #]), # Corrected: This is the actual closing of children list for app.layout.

    html.Div(id='debug-output', style={'marginTop': '20px', 'color': 'red'}),
    dcc.Store(id='current-pressing-index', data=0),
    dcc.Download(id="download-dataframe-xlsx"),
])


# NEW CALLBACK: For Export to Excel Button
@dash.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("export-excel-button", "n_clicks"),
    State("trades-table", "data"),
    prevent_initial_call=True,
)
def export_table_to_excel(n_clicks, table_data):
    if n_clicks:
        df = pd.DataFrame(table_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trading_dashboard_data_{timestamp}.xlsx"

        return dcc.send_data_frame(df.to_excel, filename=filename, index=False)
    return dash.no_update


# Callback for Cumulative P&L Line Chart
@dash.callback(
    Output(
        "cumulative-pnl-chart", "figure"
    ),  # Target the 'figure' property of the dcc.Graph
    Input("trades-table", "data"),
)
def update_cumulative_pnl_chart(rows):
    if not rows:
        # Return an empty figure or a message figure if no data
        return go.Figure().update_layout(
            title="Cumulative P&L - No Data",
            xaxis_title="Trade #",
            yaxis_title="Cumulative P&L ($)",
            xaxis={
                "visible": False,
                "showticklabels": False,
            },  # Hide axes for empty plot
            yaxis={"visible": False, "showticklabels": False},
            annotations=[
                dict(
                    text="No trade data to display cumulative P&L.",
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=16),
                )
            ],
        )

    df = pd.DataFrame(rows)
    # Ensure 'Realized P&L' is numeric, coercing errors and filling NaNs with 0
    df["Realized P&L"] = pd.to_numeric(df["Realized P&L"], errors="coerce").fillna(0)

    # Ensure 'Entry Time' is datetime, coercing errors to NaT
    df["Entry Time"] = pd.to_datetime(df["Entry Time"], errors="coerce")

    # Filter out rows where Entry Time could not be parsed or P&L is None/NaN
    df = df.dropna(subset=["Entry Time", "Realized P&L"])

    if df.empty:  # After dropping NaT, if DataFrame is empty, return empty plot
        return go.Figure().update_layout(
            title="Cumulative P&L - No Valid Data",
            xaxis_title="Trade #",
            yaxis_title="Cumulative P&L ($)",
            xaxis={"visible": False, "showticklabels": False},
            yaxis={"visible": False, "showticklabels": False},
            annotations=[
                dict(
                    text="No valid trade times or P&L to display.",
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=16),
                )
            ],
        )

    # Sort by Entry Time to ensure correct chronological cumulative sum
    df = df.sort_values(by="Entry Time")
    # Add a 'Trade Number' for plotting on x-axis if dates are too messy or duplicated
    df["Trade Number"] = range(1, len(df) + 1)
    df["Cumulative P&L"] = df["Realized P&L"].cumsum()

    fig = go.Figure(
        data=[
            go.Scatter(
                x=df["Trade Number"],
                y=df["Cumulative P&L"],
                mode="lines+markers+text",  # ADDED 'text' mode here
                name="Cumulative P&L",
                hovertemplate="Trade #: %{x}<br>Time: %{customdata|%Y-%m-%d %H:%M:%S}<br>P&L: $%{y:.2f}<extra></extra>",
                customdata=df["Entry Time"],
                # NEW: Text properties to display values on points
                text=df["Cumulative P&L"].apply(
                    lambda x: f"${x:,.2f}"
                ),  # Format text as currency
                textposition="top center",  # Position the text above the markers
            )
        ]
    )

    # Set line color based on final P&L
    final_pnl = df["Cumulative P&L"].iloc[-1]
    if final_pnl > 0:
        fig.update_traces(line=dict(color="green"))
    elif final_pnl < 0:
        fig.update_traces(line=dict(color="red"))
    else:
        fig.update_traces(line=dict(color="orange"))

    fig.update_layout(
        title="Cumulative Realized P&L Over Trades",
        xaxis_title="Trade Number",
        yaxis_title="Cumulative P&L ($)",
        hovermode="x unified",  # Shows hover info for all traces at an x-position
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor="white",  # Ensure white background for plot area
        paper_bgcolor="white",  # Ensure white background for entire paper
        font={"color": "black"},  # Default font color for readability
    )

    return fig


# NEW CALLBACK: For KPIs (Key Performance Indicators)
@dash.callback(Output("kpis-content", "children"), Input("trades-table", "data"))
def update_kpis(rows):
    if not rows:
        return html.Div(
            "No trade data to display KPIs.",
            style={"textAlign": "center", "padding": "20px"},
        )

    df = pd.DataFrame(rows)
    # Ensure Realized P&L is numeric, coercing errors and filling NaNs with 0
    df["Realized P&L"] = pd.to_numeric(df["Realized P&L"], errors="coerce").fillna(0)

    # Calculate KPIs
    total_trades = len(df)
    total_realized_pnl = df["Realized P&L"].sum()

    winning_trades = df[df["Realized P&L"] > 0]
    losing_trades = df[df["Realized P&L"] <= 0]  # Includes break-even as non-winning

    num_wins = len(winning_trades)
    num_losses = len(losing_trades)

    win_rate = (num_wins / total_trades * 100) if total_trades > 0 else 0
    avg_pnl_per_trade = (total_realized_pnl / total_trades) if total_trades > 0 else 0

    avg_win_size = (winning_trades["Realized P&L"].mean()) if num_wins > 0 else 0
    avg_loss_size = (losing_trades["Realized P&L"].mean()) if num_losses > 0 else 0

    return html.Div(
        [
            html.P(
                f"Total Trades: {total_trades}",
                style={"fontSize": "18px", "fontWeight": "bold"},
            ),
            html.P(
                f"Total Realized P&L: ${total_realized_pnl:,.2f}",
                style={"fontSize": "18px", "fontWeight": "bold"},
            ),
            html.P(
                f"Win Rate: {win_rate:,.2f}%",
                style={"fontSize": "18px", "fontWeight": "bold"},
            ),
            html.P(
                f"Avg P&L per Trade: ${avg_pnl_per_trade:,.2f}",
                style={"fontSize": "18px", "fontWeight": "bold"},
            ),
            html.P(
                f"Avg Winning Trade: ${avg_win_size:,.2f}", style={"fontSize": "18px"}
            ),
            html.P(
                f"Avg Losing Trade: ${abs(avg_loss_size):,.2f}",
                style={"fontSize": "18px"},
            ),  # Display as positive for "avg loss size"
        ],
        style={"textAlign": "center", "padding": "20px"},
    )


# NEW CALLBACK: P&L Breakdown by Category
# Callback for P&L Breakdown by Category
@dash.callback(
    Output("breakdown-content", "children"),
    Input("trades-table", "data"),
    Input("pnl-breakdown-category-filter", "value"),  # This input is already there
)
def update_pnl_breakdown_charts(rows, selected_category):
    if not rows:
        return html.Div(
            "No trade data to display P&L breakdowns.",
            style={"textAlign": "center", "padding": "20px"},
        )

    df = pd.DataFrame(rows)
    # Ensure 'Realized P&L' is numeric, coercing errors and filling NaNs with 0
    df["Realized P&L"] = pd.to_numeric(df["Realized P&L"], errors="coerce").fillna(0)

    # UPDATED: Included 'Trade came to you' and 'With Value' in all_categories
    all_categories = [
        "Entry Quality",
        "Emotional State",
        "Score",
        "Trade came to me",
        "With Value",
    ]
    charts_to_display = []

    # Determine which categories to process based on filter selection
    if selected_category == "Show All":
        categories_to_process = all_categories
    else:
        # If a specific category is selected, only process that one
        # Ensure selected_category is in all_categories to prevent errors with invalid selections
        if selected_category in all_categories:
            categories_to_process = [selected_category]
        else:  # Handle case where an invalid selection might occur (e.g., if options changed but state didn't clear)
            return html.Div(
                f"Invalid category selected: '{selected_category}'. Please select from the dropdown.",
                style={"textAlign": "center", "padding": "20px"},
            )

    for category in categories_to_process:
        # Check if the column exists and has any non-blank/non-null data for this category
        if (
            category not in df.columns
            or df[category].isnull().all()
            or (df[category] == "").all()
        ):
            charts_to_display.append(
                html.Div(
                    f"No valid data for '{category}' breakdown.",
                    style={"textAlign": "center", "padding": "10px"},
                )
            )
            continue

        # Filter out rows where the category is blank or NaN before grouping
        df_filtered = df[df[category] != ""].dropna(subset=[category])

        if df_filtered.empty:
            charts_to_display.append(
                html.Div(
                    f"No non-blank data for '{category}' breakdown.",
                    style={"textAlign": "center", "padding": "10px"},
                )
            )
            continue

        pnl_by_category = (
            df_filtered.groupby(category)["Realized P&L"].sum().reset_index()
        )
        pnl_by_category = pnl_by_category.sort_values(
            by="Realized P&L", ascending=False
        )

        # Determine bar colors (red for negative, green for positive, orange for zero)
        bar_colors = []
        for pnl in pnl_by_category["Realized P&L"]:
            if pnl < 0:
                bar_colors.append("red")
            elif pnl > 0:
                bar_colors.append("green")
            else:
                bar_colors.append("orange")

        fig = go.Figure(
            go.Bar(
                x=pnl_by_category[category],
                y=abs(
                    pnl_by_category["Realized P&L"]
                ),  # Use absolute value for y-axis to always extend upwards
                marker_color=bar_colors,
                text=pnl_by_category["Realized P&L"].apply(
                    lambda x: f"${x:,.2f}"
                ),  # Formatted P&L text
                textposition="outside",  # Text above the bars
                hovertemplate="<b>%{x}</b><br>Total P&L: $%{customdata:,.2f}<extra></extra>",  # Use customdata for hover
                customdata=pnl_by_category[
                    "Realized P&L"
                ],  # Pass original P&L for hover
            )
        )

        fig.update_layout(
            title=f"Realized P&L by {category}",
            xaxis_title=category,
            yaxis_title="Total Realized P&L ($)",
            yaxis_range=[
                0,
                max(pnl_by_category["Realized P&L"].abs().max() * 1.1, 100),
            ],  # Ensure y-axis starts at 0 and goes above max absolute PnL
            margin=dict(l=40, r=40, t=40, b=40),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font={"color": "black"},
            bargap=0.2,  # Add some gap between bars
        )
        charts_to_display.append(
            dcc.Graph(figure=fig, style={"marginBottom": "30px"})
        )  # Add spacing between charts

    if (
        not charts_to_display
    ):  # If no charts were added due to no valid data for any selected category
        return html.Div(
            "No valid trade data to display P&L breakdowns for the selected criteria.",
            style={"textAlign": "center", "padding": "20px"},
        )

    return html.Div(charts_to_display)

#####################################################################
# COMBINED CALLBACK: Handles all table updates and pressing index updates
#####################################################################
# Locate this: @dash.callback(Output('trades-table', 'data'), ...)
# REPLACE its entire content with this:

# Locate this: @dash.callback(Output('trades-table', 'data'), ...)
# REPLACE its entire content with this:

@dash.callback(
    Output('trades-table', 'data'),
    Output('current-pressing-index', 'data'),
    Output('input-trade-came-to-you', 'value'),
    Output('input-with-value', 'value'),
    Output('input-entry-quality', 'value'),
    Output('input-psychological-state', 'value'),
    Output('input-notes', 'value'),
    Output('input-score', 'value'),    
    Output('input-market-conditions', 'value'), # NEW OUTPUT for Market Conditions dropdown
    Input('add-trade-button', 'n_clicks'),
    Input('trades-table', 'data'), # This input triggers on ANY table change (add, edit, delete)
    State('trades-table', 'data_previous'),
    State('current-pressing-index', 'data'),
    State('input-trade-came-to-you', 'value'),
    State('input-with-value', 'value'),
    State('input-entry-quality', 'value'),
    State('input-psychological-state', 'value'),
    State('input-notes', 'value'),
    State('input-score', 'value'),
    State('input-market-conditions', 'value'), 
    prevent_initial_call=True
)
def handle_all_table_updates(n_clicks, current_table_data, previous_table_data, current_pressing_index,
                             trade_came_to_you_val, with_value_val, entry_quality_val, psychological_state_val, notes_val, score_val,
                             market_conditions_val):
    ctx = callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    updated_rows = list(current_table_data) # Always work with a mutable copy of the current DataTable data
    new_pressing_index = current_pressing_index # Initialize with current value from dcc.Store

    pressing_action_in_this_update = None 

    def safe_float(val):
        try:
            return float(val) if val not in [None, ''] else None
        except ValueError:
            return None

    # Define reset values for input fields (returned when 'Add Trade' button is clicked)
    reset_trade_came_to_you_val = ''
    reset_with_value_val = ''
    reset_entry_quality_val = ''
    reset_psychological_state_val = ''
    reset_notes_val = ''
    reset_score_val = ''
    reset_market_conditions_val = ''

    # --- Logic for ADDING NEW ROW via 'Add Trade' Button ---
    if trigger_id == 'add-trade-button':
        if n_clicks > 0:
            # Calculate new 'Trade #' for user-facing sequential display
            # This 'Trade #' is sequential for the session, not necessarily unique across DB
            max_existing_session_trade_num = max([r.get('Trade #', 0) for r in updated_rows if isinstance(r.get('Trade #'), (int, float))], default=0)
            trade_num = max_existing_session_trade_num + 1

            default_futures_type = config['default_futures_type']
            default_size = config['default_size']
            
            # Calculate Stop Loss and Risk for new row
            if default_futures_type in config['futures_types'] and default_size is not None and default_size > 0:
                mf = config['futures_types'][default_futures_type]['mf']
                stop_loss_pts = config['daily_risk'] / (default_size * mf)
                risk_dollars = stop_loss_pts * default_size * mf
            else:
                stop_loss_pts = None
                risk_dollars = None
                print("Warning: Could not calculate default Stop Loss/Risk for new trade. Check config or default values.")

            # Create the new row dictionary
            new_row = {
                "Trade #": trade_num,
                "Futures Type": default_futures_type,
                "Size": default_size,
                "Stop Loss (pts)": round(stop_loss_pts, 2) if stop_loss_pts is not None else "",
                "Risk ($)": round(risk_dollars, 2) if risk_dollars is not None else "",
                "Status": "Active",
                "Points Realized": "",
                "Realized P&L": "",
                "Entry Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Exit Time": "",
                "Trade came to me": trade_came_to_you_val,
                "With Value": with_value_val,
                "Score": score_val,
                "Entry Quality": entry_quality_val,
                "Emotional State": psychological_state_val,
                "Sizing": "Base",
                "Notes": notes_val,
                "Market Conditions": market_conditions_val, # NEW PROPERTY IN new_row
            }
            # Add the new row to the DataTable's current data list first
            updated_rows.append(new_row) 

            # Save the newly added trade to the SQLite database
            try:
                # db.save_trade_to_db returns the new SQLite 'id'
                new_db_id = db.save_trade_to_db(new_row)
                if new_db_id is not None:
                    new_row['id'] = new_db_id # Store the DB ID in the DataTable row (hidden column)
                    db_name, table_name = db.get_database_info()
                    print(f"New trade {new_row.get('Trade #')} added to DB '{db_name}' table '{table_name}' with ID {new_db_id}.")
                else:
                    db_name, table_name = db.get_database_info()
                    print(f"Error saving new trade {new_row.get('Trade #')} to DB '{db_name}' table '{table_name}': {e}")
                    updated_rows.pop() # Remove from DataTable if DB save truly failed
            except Exception as e:
                db_name, table_name = db.get_database_info()
                print(f"Error saving new trade {new_row.get('Trade #')} to DB '{db_name}' table '{table_name}': {e}")
            
            # Return all outputs, including reset values for input fields
            return [
                updated_rows,
                new_pressing_index,
                reset_trade_came_to_you_val,
                reset_with_value_val,
                reset_entry_quality_val,
                reset_psychological_state_val,
                reset_notes_val,
                reset_score_val,
                reset_market_conditions_val # NEW RETURN VALUE
            ]

    # --- Logic for TABLE DATA CHANGES (EDITING OR DELETING ROWS) ---
    elif trigger_id == 'trades-table':
        if previous_table_data is None: # Should not happen due to prevent_initial_call
            raise dash.exceptions.PreventUpdate

        # --- 1. Check for DELETED rows ---
        if len(current_table_data) < len(previous_table_data):
            deleted_db_ids = []
            # Find which trades (by their unique DB 'id') were deleted
            previous_db_id_map = {row.get('id'): row for row in previous_table_data if 'id' in row and row.get('id') is not None}
            current_db_ids = {row.get('id'): row for row in current_table_data if 'id' in row and row.get('id') is not None} # Changed to dict for easier lookup
            
            for db_id, row_data in previous_db_id_map.items():
                if db_id not in current_db_ids:
                    deleted_db_ids.append(db_id)
            
            for db_id in deleted_db_ids:
                try:
                    db.delete_trade_from_db(db_id) # Delete from SQLite using internal DB ID
                    db_name, table_name = db.get_database_info()
                    print(f"Trade with DB ID {db_id} deleted from DB '{db_name}' table '{table_name}'.")
                except Exception as e:
                    db_name, table_name = db.get_database_info()
                    print(f"Error deleting trade with DB ID {db_id} from DB '{db_name}' table '{table_name}': {e}")
            
            # If any rows were deleted, reset pressing index
            if deleted_db_ids:
                new_pressing_index = 0
                pressing_action_in_this_update = 'loss' # Indicate a "loss" for pressing roadmap context (e.g. invalidation)

        # --- 2. Check for MODIFIED or NEWLY PASTED rows ---
        # Convert previous data to a dict for easy lookup by 'id'
        previous_db_id_lookup = {row.get('id'): row for row in previous_table_data if 'id' in row and row.get('id') is not None}

        for i, current_row_data in enumerate(current_table_data):
            # Safely get previous row data for comparison. If current_row_data has no id or id not in lookup, previous_data will be empty dict.
            current_row_db_id = current_row_data.get('id')
            previous_row_data_at_index = previous_db_id_lookup.get(current_row_db_id, {}) 

            # Populate status_previous and points_realized_previous from previous_row_data_at_index
            status_previous = previous_row_data_at_index.get("Status")
            points_realized_previous = previous_row_data_at_index.get("Points Realized")

            # Determine if this row was modified (if existing) or is a new paste-in
            modified_or_new_row_detected = False
            
            # If it's a completely new row pasted in (has no DB ID or ID is not in previous lookup)
            if current_row_db_id is None or current_row_db_id not in previous_db_id_lookup:
                modified_or_new_row_detected = True # Force it to be detected as a new row to be saved
                
            # If the current row's content is different from its previous state based on DB ID (for existing rows)
            elif current_row_data != previous_row_data_at_index: 
                modified_or_new_row_detected = True

            if modified_or_new_row_detected:
                row_copy = current_row_data.copy() # Work with a mutable copy of the row's data
                
                # If it's a NEW row (no ID or ID not in previous lookup)
                if row_copy.get('id') is None or row_copy.get('id') not in previous_db_id_lookup:
                    # Assign a new 'Trade #' for user-facing sequential display (for pasted row)
                    max_existing_session_trade_num = max([r.get('Trade #', 0) for r in updated_rows if isinstance(r.get('Trade #'), (int, float))], default=0)
                    row_copy['Trade #'] = max_existing_session_trade_num + 1

                    # Re-calculate P&L/Risk/Exit Time for this newly pasted row (if needed)
                    futures_type_for_calc = row_copy.get("Futures Type")
                    size_for_calc = row_copy.get("Size")
                    stop_loss_pts_for_calc = row_copy.get("Stop Loss (pts)")
                    current_points_realized_for_calc = row_copy.get("Points Realized")

                    if (futures_type_for_calc in config['futures_types'] and
                        isinstance(size_for_calc, (int, float)) and size_for_calc is not None and size_for_calc > 0 and
                        isinstance(stop_loss_pts_for_calc, (int, float)) and stop_loss_pts_for_calc is not None):
                        mf = config['futures_types'][futures_type_for_calc]['mf']
                        calculated_risk_dollars = size_for_calc * stop_loss_pts_for_calc * mf
                        row_copy["Risk ($)"] = round(calculated_risk_dollars, 2)
                    else:
                        row_copy["Risk ($)"] = None
                    
                    if (current_points_realized_for_calc not in [None, ''] and
                        futures_type_for_calc in config['futures_types'] and
                        isinstance(size_for_calc, (int, float)) and size_for_calc is not None and size_for_calc > 0):
                        try:
                            points_realized_num_for_calc = float(current_points_realized_for_calc)
                            mf = config['futures_types'][futures_type_for_calc]['mf']
                            calculated_pnl = size_for_calc * points_realized_num_for_calc * mf
                            row_copy["Realized P&L"] = round(calculated_pnl, 2)
                            pnl_was_calculated_and_is_conclusive = True
                        except ValueError:
                            row_copy["Realized P&L"] = None
                    else:
                        row_copy["Realized P&L"] = ""
                    
                    # Assign default status and entry/exit time for pasted rows if not set
                    if not row_copy.get("Status"): row_copy["Status"] = "Active"
                    if not row_copy.get("Entry Time"): row_copy["Entry Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Save the newly pasted row to the database and get its DB ID
                    try:
                        new_db_id = db.save_trade_to_db(row_copy)
                        if new_db_id is not None:
                            row_copy['id'] = new_db_id # Store DB ID
                            db_name, table_name = db.get_database_info()
                            print(f"New trade {row_copy.get('Trade #')} (pasted) saved to DB '{db_name}' table '{table_name}' with ID {new_db_id}.")
                        else:
                            db_name, table_name = db.get_database_info()
                            print(f"Failed to get DB ID for pasted trade {row_copy.get('Trade #')}, DB save likely failed.")
                            # Consider returning initial data or error message
                    except Exception as e:
                        db_name, table_name = db.get_database_info()
                        print(f"Error saving pasted trade {row_copy.get('Trade #')} to DB '{db_name}' table '{table_name}': {e}")
                        pass

                else: # It's an existing row that was modified (has an ID, and was in previous_db_id_lookup)
                    # Apply recalculation and pressing logic, then update DB
                    status_current = row_copy.get("Status")
                    points_realized_current = row_copy.get("Points Realized")
                    
                    should_recalculate_pnl = False
                    if (current_row_data.get("Futures Type") != previous_row_data_at_index.get("Futures Type") or
                        current_row_data.get("Size") != previous_row_data_at_index.get("Size") or
                        current_row_data.get("Stop Loss (pts)") != previous_row_data_at_index.get("Stop Loss (pts)") or
                        current_row_data.get("Points Realized") != previous_row_data_at_index.get("Points Realized") or
                        current_row_data.get("Status") != previous_row_data_at_index.get("Status")): # Corrected: Removed typo
                        should_recalculate_pnl = True
                    
                    pnl_was_calculated_and_is_conclusive = False
                    if should_recalculate_pnl:
                        futures_type = row_copy.get("Futures Type")
                        size = row_copy.get("Size")
                        stop_loss_pts = row_copy.get("Stop Loss (pts)")
                        current_points_realized_for_calc = row_copy.get("Points Realized")

                        if (futures_type in config['futures_types'] and
                            isinstance(size, (int, float)) and size is not None and size > 0 and
                            isinstance(stop_loss_pts, (int, float)) and stop_loss_pts is not None):
                            mf = config['futures_types'][futures_type]['mf']
                            calculated_risk_dollars = size * stop_loss_pts * mf
                            row_copy["Risk ($)"] = round(calculated_risk_dollars, 2)
                        else:
                            row_copy["Risk ($)"] = None
                        
                        if (current_points_realized_for_calc not in [None, ''] and
                            futures_type in config['futures_types'] and
                            isinstance(size, (int, float)) and size is not None and size > 0):
                            try:
                                points_realized_num_for_calc = float(current_points_realized_for_calc)
                                mf = config['futures_types'][futures_type]['mf']
                                calculated_pnl = size * points_realized_num_for_calc * mf
                                row_copy["Realized P&L"] = round(calculated_pnl, 2)
                                pnl_was_calculated_and_is_conclusive = True
                            except ValueError:
                                row_copy["Realized P&L"] = None
                        else:
                            row_copy["Realized P&L"] = ""
                    
                    # Update Exit Time and Status based on Pts Realized change
                    # if (points_realized_current not in [None, ''] and status_current != "Closed"):
                    #      row_copy["Status"] = "Closed"
                    #      if not row_copy.get("Exit Time"):
                    #          row_copy["Exit Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # elif (points_realized_current is None and points_realized_previous is not None and status_current != "Active"):
                    #      row_copy["Status"] = "Active"
                    #      row_copy["Realized P&L"] = ""
                    #      row_copy["Exit Time"] = ""
                    #      new_pressing_index = 0
                    #      pressing_action_in_this_update = 'loss'
                    # NEW LOGIC: Update Status to Win/Lose/BE and fill Exit Time based on Realized P&L
                    # This block runs after Realized P&L is calculated for the row_copy.
                    calculated_pnl_for_status = safe_float(row_copy.get("Realized P&L"))

                    if calculated_pnl_for_status is not None:
                        if calculated_pnl_for_status > 0:
                            new_status_text = "Win"
                        elif calculated_pnl_for_status < 0:
                            new_status_text = "Loss"
                        else: # calculated_pnl_for_status == 0
                            new_status_text = "BE" # Break-Even

                        # Only change Status and Exit Time if it's not already set to this status
                        # and if Points Realized just became a value, or value changed meaningfully.
                        if row_copy.get("Status") != new_status_text: # Prevent redundant updates
                            if points_realized_current not in [None, ''] and points_realized_previous in [None, '']:
                                # Only set Exit Time if Points Realized was just entered (from blank)
                                if not row_copy.get("Exit Time"):
                                    row_copy["Exit Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            elif points_realized_current not in [None, ''] and points_realized_previous not in [None, ''] and points_realized_current != points_realized_previous:
                                # If Points Realized changed, but was already non-blank, also set exit time
                                if not row_copy.get("Exit Time"):
                                    row_copy["Exit Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            row_copy["Status"] = new_status_text # Update Status text

                    elif points_realized_current is None and previous_row_data_at_index.get("Points Realized") is not None:
                        # If Points Realized was cleared, revert Status and P&L/Exit Time
                        row_copy["Status"] = "Active" # Or initial status if cleared
                        row_copy["Realized P&L"] = ""
                        row_copy["Exit Time"] = ""
                        new_pressing_index = 0
                        pressing_action_in_this_update = 'loss' # Reset pressing roadmap if a finalized trade is un-finalized

                    # Update in DB (using the 'id' of the row)
                    try:
                        db.update_trade_in_db(row_copy['id'], row_copy)
                        db_name, table_name = db.get_database_info()
                        print(f"Trade with DB ID {row_copy.get('id')} updated in DB '{db_name}' table '{table_name}' (from modification).")
                    except Exception as e:
                        db_name, table_name = db.get_database_info()
                        print(f"Error updating trade with DB ID {row_copy.get('id')} in DB '{db_name}' table '{table_name}' (from modification): {e}")

                    # Evaluate pressing roadmap for this modified row if conclusive                 
                    if pnl_was_calculated_and_is_conclusive and row_copy.get("Status") in ["Win", "Lose", "BE"]: # CHANGED: Check for new Status values
                        final_pnl_for_pressing_eval = safe_float(row_copy.get("Realized P&L"))
                        if final_pnl_for_pressing_eval is not None:
                            if final_pnl_for_pressing_eval > 0:
                                pressing_action_in_this_update = 'win'
                            elif final_pnl_for_pressing_eval <= 0:
                                pressing_action_in_this_update = 'loss'
                    
                updated_rows[i] = row_copy # Ensure updated row_copy is in the list to be returned
            
        # Determine final pressing index after iterating through all potential row changes
        pressing_sequence_full = config.get("pressing_sequence_multipliers", [1, 2, 1.5, 3])
        max_pressing_index_full = len(pressing_sequence_full) - 1

        if pressing_action_in_this_update == 'win':
            if current_pressing_index == max_pressing_index_full:
                new_pressing_index = 0
            else:
                new_pressing_index = current_pressing_index + 1
        elif pressing_action_in_this_update == 'loss':
            new_pressing_index = 0
            
    return [
        updated_rows, # This is the final state of the DataTable
        new_pressing_index,
        dash.no_update, # These output values are only for 'Add Trade' branch
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    ]

#####################################################################
# CALLBACK: Update trades-table data based on DatePickerSingle selection
#####################################################################
@dash.callback(
    Output('trades-table', 'data', allow_duplicate=True), # Output to the DataTable
    Input('date-picker-single', 'date'), # Trigger when date picker value changes
    prevent_initial_call=True
)
def update_daily_table_from_date_picker(selected_date):
    if selected_date is None:
        # If date is cleared, return an empty table or no_update
        return [] # Empty table if no date selected
    
    try:
        # Fetch trades for the selected date
        selected_datetime_date = pd.to_datetime(selected_date).date() # Ensure it's a date object
        trades_for_selected_date = db.fetch_trades_by_date(selected_datetime_date)
        
        db_name, table_name = db.get_database_info()
        print(f"Loaded {len(trades_for_selected_date)} trades for {selected_datetime_date} from DB '{db_name}' table '{table_name}' via DatePicker.")
        
        return trades_for_selected_date
    except Exception as e:
        print(f"Error updating table from DatePicker for date {selected_date}: {e}")
        return [] # Return empty list on error

# Other callbacks (Cumulative P&L, KPIs, P&L Breakdown, etc.) in pages/daily_helper.py
# update_cumulative_pnl_chart
# update_kpis
# update_pnl_breakdown_charts
# update_available_risk_gauge
# update_pnl_progress_bar
# update_trades_progress_bar
# update_pressing_roadmap_visual

# These analytics callbacks should filter by 'date-picker-single' (for daily data)
# Most of them already do, or can be adapted easily.


# Callback for Available Risk Gauge
@dash.callback(
    Output("available-risk-gauge", "figure"),
    Input("trades-table", "data"),
    Input(
        "date-picker-single", "date"
    ),  # Assuming this input is already added in layout
)
def update_available_risk_gauge(rows, selected_date):
    daily_risk_limit = config["daily_risk"]

    df_all_trades = pd.DataFrame(rows)
    # NEW: Robustly handle 'Entry Time' column
    if "Entry Time" in df_all_trades.columns and not df_all_trades["Entry Time"].empty:
        df_all_trades["Entry Time"] = pd.to_datetime(
            df_all_trades["Entry Time"], errors="coerce"
        ).dt.date
        # Filter data for the selected date only for daily metrics
        if selected_date is not None:
            selected_datetime = pd.to_datetime(selected_date).date()
            df_filtered = df_all_trades[
                df_all_trades["Entry Time"] == selected_datetime
            ]
        else:
            df_filtered = (
                df_all_trades  # If no date selected, consider all current data
            )
    else:
        df_filtered = (
            pd.DataFrame()
        )  # If 'Entry Time' is missing or empty, filter results in empty DataFrame

    if df_filtered.empty:
        available_risk = daily_risk_limit
        active_risk = 0
        realized_pnl = 0
    else:
        df_filtered["Risk ($)"] = pd.to_numeric(
            df_filtered["Risk ($)"], errors="coerce"
        ).fillna(0)
        df_filtered["Realized P&L"] = pd.to_numeric(
            df_filtered["Realized P&L"], errors="coerce"
        ).fillna(0)

        active_risk = df_filtered[df_filtered["Status"] == "Active"]["Risk ($)"].sum()        
        realized_pnl = df_filtered[df_filtered["Status"].isin(["Win", "Lose", "BE"])]["Realized P&L"].sum()

        available_risk = max(0, daily_risk_limit + realized_pnl - active_risk)

    max_range = max(daily_risk_limit * 1.2, available_risk * 1.1)
    if config.get("profit_target") and config["profit_target"] > 0:
        max_range = max(max_range, config["profit_target"] * 1.1)

    steps = [
        {"range": [0, daily_risk_limit * 0.2], "color": "red"},
        {"range": [daily_risk_limit * 0.2, daily_risk_limit * 0.6], "color": "orange"},
        {"range": [daily_risk_limit * 0.6, daily_risk_limit], "color": "yellowgreen"},
        {"range": [daily_risk_limit, max_range], "color": "green"},
    ]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=available_risk,
            domain={"x": [0, 1], "y": [0, 1]},
            #title={"text": "Available Risk", "font": {"size": 16}},
            title={
            "text": "Available Risk",
                "font": {
                    "family": "Segoe UI, sans-serif",
                    "size": 18,
                    "color": "#2c3e50"
                }
            },
            gauge={
                "axis": {
                    "range": [0, max_range],
                    "tickwidth": 1,
                    "tickcolor": "darkblue",
                    "nticks": 5,
                },
                "bar": {"color": "rgba(0,0,0,0)"},
                "steps": steps,
                "threshold": {
                    "line": {"color": "black", "width": 3},
                    "thickness": 0.75,
                    "value": daily_risk_limit,
                },
            },
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        #paper_bgcolor="white",
        paper_bgcolor="#f0f2f5", # CHANGED to match page background
        font={"color": "black", "family": "Arial"},
    )
    return fig


# Callback for Realized P&L Progress Bar
@dash.callback(
    Output("pnl-progress-bar-container", "children"),
    Input("trades-table", "data"),
    Input(
        "date-picker-single", "date"
    ),  # Assuming this input is already added in layout
)
def update_pnl_progress_bar(rows, selected_date):
    profit_target = config.get("profit_target", 1)
    total_realized_pnl = 0

    df_all_trades = pd.DataFrame(rows)
    # NEW: Robustly handle 'Entry Time' column
    if "Entry Time" in df_all_trades.columns and not df_all_trades["Entry Time"].empty:
        df_all_trades["Entry Time"] = pd.to_datetime(
            df_all_trades["Entry Time"], errors="coerce"
        ).dt.date
        # Filter data for the selected date only
        if selected_date is not None:
            selected_datetime = pd.to_datetime(selected_date).date()
            df_filtered = df_all_trades[
                df_all_trades["Entry Time"] == selected_datetime
            ]
        else:
            df_filtered = pd.DataFrame(
                rows
            )  # If no date selected, consider all current data
    else:
        df_filtered = (
            pd.DataFrame()
        )  # If 'Entry Time' is missing or empty, filter results in empty DataFrame

    if df_filtered.empty:
        total_realized_pnl = 0
    else:
        df_filtered["Realized P&L"] = pd.to_numeric(
            df_filtered["Realized P&L"], errors="coerce"
        ).fillna(0)
        total_realized_pnl = df_filtered["Realized P&L"].sum()

    progress_val = abs(total_realized_pnl)

    percent = (progress_val / profit_target) * 100 if profit_target != 0 else 0
    percent = max(min(percent, 100), 0)

    if total_realized_pnl < 0:
        bar_color = "linear-gradient(to right, #ffc1c1, #ff4d4d, #cc0000)"
        text_color = "white"
        pnl_text = f"-${abs(total_realized_pnl):,.2f}"
    else:
        bar_color = "linear-gradient(to right, #e6ffe6, #66cc66, #008000)"
        text_color = "white"
        pnl_text = f"+${total_realized_pnl:,.2f}"

    main_bar_visual_div = html.Div(
        style={
            "backgroundColor": "#e0e0e0",
            "borderRadius": "20px",
            "height": "30px",
            "position": "relative",
            "overflow": "hidden",
            "boxShadow": "inset 0 1px 3px rgba(0,0,0,0.2)",
        },
        children=[
            html.Div(
                style={
                    "background": bar_color,
                    "width": f"{percent}%",
                    "height": "100%",
                    "borderRadius": "20px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "fontWeight": "bold",
                    "color": text_color,
                    "fontSize": "14px",
                    "transition": "width 0.5s ease-in-out",
                },
                children=[pnl_text],
            ),
            (
                html.Div(
                    "🏁",
                    style={
                        "position": "absolute",
                        "right": "6px",
                        "top": "2px",
                        "fontSize": "20px",
                        "zIndex": 2,
                    },
                )
                if profit_target > 0
                else None
            ),
        ],
        className='progress-bar-container' 
    )

    target_display_div = html.Div(
        f"Target: ${profit_target:,.2f}",
        style={
            "textAlign": "right",
            "fontSize": "12px",
            "color": "#555",
            "marginTop": "2px",
        },
    )

    return [main_bar_visual_div, target_display_div]


# Callback for Trades per Day Progress Bar
@dash.callback(
    Output("trades-progress-bar-container", "children"),
    Input("trades-table", "data"),
    Input(
        "date-picker-single", "date"
    ),  # Assuming this input is already added in layout
)
def update_trades_progress_bar(rows, selected_date):
    max_trades = config.get("max_trades_per_day", 1)

    df_all_trades = pd.DataFrame(rows)

    # NEW: Robustly handle 'Entry Time' column
    if "Entry Time" in df_all_trades.columns and not df_all_trades["Entry Time"].empty:
        df_all_trades["Entry Time"] = pd.to_datetime(
            df_all_trades["Entry Time"], errors="coerce"
        ).dt.date
        # Filter data for the selected date only
        if selected_date is not None:
            selected_datetime = pd.to_datetime(selected_date).date()
            df_filtered = df_all_trades[
                df_all_trades["Entry Time"] == selected_datetime
            ]
        else:
            df_filtered = (
                df_all_trades  # If no date selected, consider all current data
            )
    else:
        df_filtered = (
            pd.DataFrame()
        )  # If 'Entry Time' is missing or empty, filter results in empty DataFrame

    current_trades = len(df_filtered)  # Use length of filtered data

    percent_used = (current_trades / max_trades) * 100 if max_trades > 0 else 0
    percent_used = max(min(percent_used, 100), 0)

    if percent_used <= 30:
        bar_color = "linear-gradient(to right, #e6ffe6, #66cc66, #008000)"
    elif percent_used <= 60:
        bar_color = "linear-gradient(to right, #FFFACD, #FFD700, #DAA520)"
    else:
        bar_color = "linear-gradient(to right, #ffc1c1, #ff4d4d, #cc0000)"

    display_text = f"{current_trades}/{max_trades}"

    return html.Div(
        style={
            "backgroundColor": "#e0e0e0",
            "borderRadius": "20px",
            "height": "30px",
            "position": "relative",
            "overflow": "hidden",
            "boxShadow": "inset 0 1px 3px rgba(0,0,0,0.2)",
        },
        children=[
            html.Div(
                style={
                    "background": bar_color,
                    "width": f"{percent_used}%",
                    "height": "100%",
                    "borderRadius": "20px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "fontWeight": "bold",
                    "color": "white",
                    "fontSize": "14px",
                    "transition": "width 0.5s ease-in-out",
                },
                children=[display_text],
            )
        ],
        className='progress-bar-container' 
    )


# Callback for Pressing Roadmap visual
@dash.callback(
    Output("pressing-roadmap-container", "children"),
    Input("current-pressing-index", "data"),
)
def update_pressing_roadmap_visual(current_pressing_index):
    pressing_sequence_multipliers = config.get(
        "pressing_sequence_multipliers", [1, 2, 1.5, 3]
    )
    default_size = config.get("default_size", 1)

    roadmap_elements = []

    roadmap_elements.append(
        html.Span("🚀 ", style={"fontSize": "20px", "marginRight": "5px"})
    )

    for idx, multiplier in enumerate(pressing_sequence_multipliers):
        display_size_val = multiplier * default_size
        display_text = (
            str(int(display_size_val))
            if display_size_val == int(display_size_val)
            else str(display_size_val)
        )

        color = "#fdd835" if idx == current_pressing_index else "#90caf9"
        text_color = "#000000" if idx == current_pressing_index else "#ffffff"

        box_style = {
            "backgroundColor": color,
            "color": text_color,
            "borderRadius": "4px",
            "padding": "8px 12px",
            "fontWeight": "bold",
            "marginRight": "6px",
            "minWidth": "36px",
            "textAlign": "center",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.2)",
            "transition": "all 0.3s ease-in-out",
            "border": "1px solid "
            + ("#DAA520" if idx == current_pressing_index else "#42a5f5"),
        }

        roadmap_elements.append(html.Div(display_text, style=box_style))

        if idx < len(pressing_sequence_multipliers) - 1:
            roadmap_elements.append(
                html.Div(
                    style={
                        "borderTop": "3px solid #42a5f5",
                        "width": "30px",
                        "marginRight": "6px",
                    }
                )
            )

    roadmap_elements.append(
        html.Span(" ➡️", style={"fontSize": "20px", "marginLeft": "5px"})
    )

    return roadmap_elements


# if __name__ == "__main__":
#     app.run(debug=True)