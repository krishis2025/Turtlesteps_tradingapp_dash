import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table, callback_context
import json
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import io # For dcc.send_data_frame
import base64 # Needed for load_trades_json

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

# Register this page with Dash
dash.register_page(
    __name__,
    path='/',  # This makes 'daily_helper.py' the default page at the root URL
    name='Daily Helper', # Name that will appear in navigation links
    title='Trading Dashboard - Daily Helper',
    description='Daily trade entry and monitoring.'
)

# Initial empty data for the table
initial_data = []
# --- Layout for the Daily Helper Page ---
layout = html.Div([
    #html.H2("Trading Dashboard - Daily Helper", style={'textAlign': 'center', 'marginBottom': '20px'}),


    # Main Dashboard Content (pulled out from Home tab, now directly in app.layout)
    html.Div(id="home-tab-content-wrapper", style={'padding': '20px', 'minHeight': '800px'}, children=[
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
                html.H3("Available Risk", style={'textAlign': 'center', 'marginTop': '0', 'marginBottom': '5px'}),
                dcc.Graph(id='available-risk-gauge', config={'displayModeBar': False},
                          style={'height': '180px'}) 
            ], style={'flex': '1 1 350px', 'paddingRight': '10px', 'boxSizing': 'border-box'}), # Changed flex-basis to 350px, added boxSizing

            # Column 2: Stacked Progress Bars and Placeholder
            html.Div([
                # Row 1: Realized P&L Progress Bar
                html.Div([
                    html.H3("Realized P&L Progress", style={'textAlign': 'center', 'marginTop': '0', 'marginBottom': '5px'}),
                    html.Div(id='pnl-progress-bar-container', style={'width': '100%', 'height': 'auto'}),
                ], style={'width': '100%', 'height': 'auto', 'maxWidth': '100%', 'boxSizing': 'border-box', 'marginBottom': '15px'}), # Added maxWidth: '100%', boxSizing

                # Row 2: Trades per Day Progress Bar
                html.Div([
                    html.H3("Trades per Day", style={'textAlign': 'center', 'marginTop': '0', 'marginBottom': '5px'}),
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

            ], style={'flex': '1 1 350px', 'paddingLeft': '10px', 'boxSizing': 'border-box', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-around'}), # Changed flex-basis to 350px, added boxSizing
        ], style={
            'display': 'flex',
            'flexWrap': 'wrap', # CRUCIAL: Confirmed to be here
            'justifyContent': 'space-around',
            'alignItems': 'flex-start',
            'width': '100%',
            'marginBottom': '20px',
            'boxSizing': 'border-box' # Ensures padding/border are included in the width
        }),

        # Export to Excel Button
        html.Div([
            html.Button("Export to Excel", id="export-excel-button", n_clicks=0,
                        style={'marginBottom': '10px', 'padding': '8px 15px', 'fontSize': '14px', 'cursor': 'pointer'})
        ], style={'textAlign': 'left', 'width': '95%', 'margin': '0 auto'}),

        # DataTable
        html.Div([
            dash_table.DataTable(
                id='trades-table',
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
                data=initial_data,
                editable=True,
                row_deletable=True,
                dropdown={
                    'Futures Type': {
                        'options': [{'label': i, 'value': i} for i in config['futures_types'].keys()],
                        'clearable': False
                    },
                    'Status': {
                        'options': [{'label': i, 'value': i} for i in ['Active', 'Closed']],
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
                            {'label': 'Waited Patiently', 'value': 'Waited Patiently'},
                            {'label': 'Calm / Standard', 'value': 'Calm / Standard'},
                            {'label': 'Impulsive / FOMO', 'value': 'Impulsive / FOMO'},
                            {'label': 'Hesitant / Missed', 'value': 'Hesitant / Missed'},
                            {'label': 'Forced / Overtraded', 'value': 'Forced / Overtraded'},
                        ],
                        'clearable': False
                    },
                    'Emotional State': {
                        'options': [
                            {'label': ' ', 'value': ''},
                            {'label': 'Calm / Disciplined', 'value': 'Calm / Disciplined'},
                            {'label': 'Get back losses', 'value': 'Get back losses'},
                            {'label': 'FOMO', 'value': 'FOMO'},
                            {'label': 'Fear of giving away profit', 'value': 'Fear of giving away profit'},
                            {'label': 'Overconfidence', 'value': 'Overconfidence'},
                            {'label': 'Frustration / Impatience', 'value': 'Frustration / Impatience'},
                            {'label': 'Distracted', 'value': 'Distracted'},
                        ],
                        'clearable': False
                    },
                    'Sizing': {
                        'options': [{'label': i, 'value': i} for i in ['Base', 'Increased', 'Reduced']],
                        'clearable': False
                    },
                },
                style_data_conditional=[
                    {
                        'if': {
                            'filter_query': '{Risk ($)} > ' + str(config['daily_risk'])
                        },
                        'backgroundColor': '#FF4136',
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Realized P&L} < 0'
                        },
                        'backgroundColor': '#F08080', # LightCoral for loss
                        'color': 'black'
                    },
                    {
                        'if': {
                            'filter_query': '{Realized P&L} > 0'
                        },
                        'backgroundColor': '#90EE90', # LightGreen for profit
                        'color': 'black'
                    },
                    {
                        'if': {
                            'filter_query': '{Realized P&L} = 0'
                        },
                        'backgroundColor': '#FFD700', # Gold for break-even
                        'color': 'black'
                    }
                ],
                style_cell={
                    'textAlign': 'left',
                    'padding': '5px',
                    'fontFamily': 'sans-serif',
                    'minWidth': 80, 'width': 80, 'maxWidth': 180
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold',
                    'textAlign': 'center'
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
        ], style={'marginTop': '20px', 'marginBottom': '20px', 'width': '95%', 'margin': '0 auto', 'overflowX': 'auto'}), # ADDED overflowX: 'auto'

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

                ], style={'flex': '1 1 280px', 'padding': '0 10px', 'boxSizing': 'border-box'}), # Changed flex-basis to 280px, added boxSizing

                # Column 2
                html.Div([
                    #Row1: Entry Quality
                    html.Div([
                        html.Label("Entry Quality:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                        dcc.Dropdown(
                            id='input-entry-quality',
                            options=[
                                {'label': ' ', 'value': ''},
                                {'label': 'Waited Patiently', 'value': 'Waited Patiently'},
                                {'label': 'Calm / Standard', 'value': 'Calm / Standard'},
                                {'label': 'Impulsive / FOMO', 'value': 'Impulsive / FOMO'},
                                {'label': 'Hesitant / Missed', 'value': 'Hesitant / Missed'},
                                {'label': 'Forced / Overtraded', 'value': 'Forced / Overtraded'},
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
                                {'label': 'Calm / Disciplined', 'value': 'Calm / Disciplined'},
                                {'label': 'Get back losses', 'value': 'Get back losses'},
                                {'label': 'FOMO', 'value': 'FOMO'},
                                {'label': 'Fear of giving away profit', 'value': 'Fear of giving away profit'},
                                {'label': 'Overconfidence', 'value': 'Overconfidence'},
                                {'label': 'Frustration / Impatience', 'value': 'Frustration / Impatience'},
                                {'label': 'Distracted', 'value': 'Distracted'},
                            ],
                            value='',
                            clearable=False,
                            style={'width': '100%'}
                        )
                    ], style={'marginBottom': '15px'}),
                    #Row3: Sizing
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

                ], style={'flex': '1 1 280px', 'padding': '0 10px', 'boxSizing': 'border-box', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-between'}), # Changed flex-basis to 280px, added boxSizing

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
                ], style={'flex': '1 1 280px', 'padding': '0 10px', 'boxSizing': 'border-box', 'display': 'flex', 'flexDirection': 'column'}), # Changed flex-basis to 280px, added boxSizing

            ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'alignItems': 'flex-start', 'width': '100%', 'marginBottom': '20px', 'boxSizing': 'border-box'}), # ADDED boxSizing

        ], style={'border': '1px solid #ddd', 'borderRadius': '5px', 'padding': '20px', 'marginTop': '20px', 'marginBottom': '20px'}),
         

        # Add Trade button (Moved here, and is now the only one)
        html.Div([
            html.Button('Add Trade', id='add-trade-button', n_clicks=0, style={'marginBottom': '20px', 'padding': '12px 25px', 'fontSize': '18px', 'cursor': 'pointer'})
        ], style={'textAlign': 'left', 'width': '95%', 'margin': '0 auto'}),
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


# COMBINED CALLBACK: Handles all table and pressing index updates
@dash.callback(
    Output("trades-table", "data"),
    Output("current-pressing-index", "data"),
    Output("input-trade-came-to-you", "value"),
    Output("input-with-value", "value"),
    Output("input-entry-quality", "value"),
    Output("input-psychological-state", "value"),
    Output("input-notes", "value"),
    Output("input-score", "value"),
    Input("add-trade-button", "n_clicks"),
    Input("trades-table", "data"),
    State("trades-table", "data_previous"),
    State("current-pressing-index", "data"),
    State("input-trade-came-to-you", "value"),
    State("input-with-value", "value"),
    State("input-entry-quality", "value"),
    State("input-psychological-state", "value"),
    State("input-notes", "value"),
    State("input-score", "value"),
    prevent_initial_call=True,
)
def handle_all_table_updates(
    n_clicks,
    current_table_data,
    previous_table_data,
    current_pressing_index,
    trade_came_to_you_val,
    with_value_val,
    entry_quality_val,
    psychological_state_val,
    notes_val,
    score_val,
):
    ctx = callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    updated_rows = current_table_data
    new_pressing_index = current_pressing_index

    pressing_action_in_this_update = None

    def safe_float(val):
        try:
            return float(val) if val not in [None, ""] else None
        except ValueError:
            return None

    reset_trade_came_to_you_val = ""
    reset_with_value_val = ""
    reset_entry_quality_val = ""
    reset_psychological_state_val = ""
    reset_notes_val = ""
    reset_score_val = ""

    # --- Logic for Add Trade Button ---
    if trigger_id == "add-trade-button":
        if n_clicks > 0:
            rows_to_modify = (
                list(current_table_data) if current_table_data is not None else []
            )
            trade_num = len(rows_to_modify) + 1
            default_futures_type = config["default_futures_type"]
            default_size = config["default_size"]

            if (
                default_futures_type in config["futures_types"]
                and default_size is not None
                and default_size > 0
            ):
                mf = config["futures_types"][default_futures_type]["mf"]
                stop_loss_pts = config["daily_risk"] / (default_size * mf)
                risk_dollars = stop_loss_pts * default_size * mf
            else:
                stop_loss_pts = None
                risk_dollars = None
                print(
                    "Warning: Could not calculate default Stop Loss/Risk. Check config or default values."
                )

            new_row = {
                "Trade #": trade_num,
                "Futures Type": default_futures_type,
                "Size": default_size,
                "Stop Loss (pts)": (
                    round(stop_loss_pts, 2) if stop_loss_pts is not None else ""
                ),
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
            }
            rows_to_modify.append(new_row)
            updated_rows = rows_to_modify

            return [
                updated_rows,
                new_pressing_index,
                reset_trade_came_to_you_val,
                reset_with_value_val,
                reset_entry_quality_val,
                reset_psychological_state_val,
                reset_notes_val,
                reset_score_val,
            ]

    # --- Logic for Table Data Changes ---
    elif trigger_id == "trades-table":
        if previous_table_data is None:
            raise dash.exceptions.PreventUpdate

        updated_rows_from_table_logic = []

        pressing_sequence = config.get("pressing_sequence_multipliers", [1, 2, 1.5, 3])
        max_pressing_index = len(pressing_sequence) - 1

        for i, row in enumerate(current_table_data):
            row_copy = row.copy()

            is_existing_row = i < len(previous_table_data)

            status_current = row_copy.get("Status")
            status_previous = (
                previous_table_data[i].get("Status") if is_existing_row else None
            )

            points_realized_current = row_copy.get("Points Realized")
            points_realized_previous = (
                previous_table_data[i].get("Points Realized")
                if is_existing_row
                else None
            )

            points_realized_current_num = safe_float(points_realized_current)
            points_realized_previous_num = safe_float(points_realized_previous)

            if (
                points_realized_current_num is not None
                and points_realized_previous_num is None
            ):
                row_copy["Status"] = "Closed"
                if not row_copy.get("Exit Time"):
                    row_copy["Exit Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            elif (
                points_realized_current_num is None
                and points_realized_previous_num is not None
            ):
                row_copy["Status"] = "Active"
                row_copy["Realized P&L"] = ""
                row_copy["Exit Time"] = ""
                pressing_action_in_this_update = "loss"

            should_recalculate_pnl = False
            if (
                points_realized_current != points_realized_previous
                or status_current != status_previous
                or row_copy.get("Futures Type")
                != (
                    previous_table_data[i].get("Futures Type")
                    if is_existing_row
                    else None
                )
                or row_copy.get("Size")
                != (previous_table_data[i].get("Size") if is_existing_row else None)
                or row_copy.get("Stop Loss (pts)")
                != (
                    previous_table_data[i].get("Stop Loss (pts)")
                    if is_existing_row
                    else None
                )
            ):
                should_recalculate_pnl = True

            elif not is_existing_row and i == len(current_table_data) - 1:
                should_recalculate_pnl = True

            pnl_was_calculated_and_is_conclusive = False
            if should_recalculate_pnl:
                futures_type = row_copy.get("Futures Type")
                size = row_copy.get("Size")
                stop_loss_pts = row_copy.get("Stop Loss (pts)")
                current_points_realized_for_calc = row_copy.get("Points Realized")

                if (
                    futures_type in config["futures_types"]
                    and isinstance(size, (int, float))
                    and size is not None
                    and size > 0
                    and isinstance(stop_loss_pts, (int, float))
                    and stop_loss_pts is not None
                ):
                    mf = config["futures_types"][futures_type]["mf"]
                    calculated_risk_dollars = size * stop_loss_pts * mf
                    row_copy["Risk ($)"] = round(calculated_risk_dollars, 2)
                else:
                    row_copy["Risk ($)"] = None

                if (
                    current_points_realized_for_calc not in [None, ""]
                    and futures_type in config["futures_types"]
                    and isinstance(size, (int, float))
                    and size is not None
                    and size > 0
                ):
                    try:
                        points_realized_num_for_calc = float(
                            current_points_realized_for_calc
                        )
                        mf = config["futures_types"][futures_type]["mf"]
                        calculated_pnl = size * points_realized_num_for_calc * mf
                        row_copy["Realized P&L"] = round(calculated_pnl, 2)
                        pnl_was_calculated_and_is_conclusive = True
                    except ValueError:
                        row_copy["Realized P&L"] = None
                else:
                    row_copy["Realized P&L"] = ""

            updated_rows_from_table_logic.append(row_copy)

            if (
                pnl_was_calculated_and_is_conclusive
                and row_copy.get("Status") == "Closed"
            ):
                final_pnl_for_pressing_eval = safe_float(row_copy.get("Realized P&L"))

                if final_pnl_for_pressing_eval is not None:
                    if final_pnl_for_pressing_eval > 0:
                        pressing_action_in_this_update = "win"
                    elif final_pnl_for_pressing_eval <= 0:
                        pressing_action_in_this_update = "loss"

        updated_rows = updated_rows_from_table_logic

        pressing_sequence_full = config.get(
            "pressing_sequence_multipliers", [1, 2, 1.5, 3]
        )
        max_pressing_index_full = len(pressing_sequence_full) - 1

        if pressing_action_in_this_update == "win":
            if current_pressing_index == max_pressing_index_full:
                new_pressing_index = 0
            else:
                new_pressing_index = current_pressing_index + 1
        elif pressing_action_in_this_update == "loss":
            new_pressing_index = 0

    return [
        updated_rows,
        new_pressing_index,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    ]


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
        realized_pnl = df_filtered[df_filtered["Status"] == "Closed"][
            "Realized P&L"
        ].sum()

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
            title={"text": "Available Risk", "font": {"size": 16}},
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
        paper_bgcolor="white",
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
