import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import json
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go # Import for Gauge

# Load config
CONFIG_FILE = 'config.json'
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Error: {CONFIG_FILE} not found. Please create it with the specified structure.")
    exit()

app = dash.Dash(__name__)

# Initial empty data for the table
initial_data = []

app.layout = html.Div([
    html.H2("Trading Dashboard", style={'textAlign': 'center', 'margin-bottom': '20px'}),
    html.Button('Add Trade', id='add-trade-button', n_clicks=0, style={'margin-bottom': '10px', 'padding': '10px 20px', 'fontSize': '16px', 'cursor': 'pointer'}),

    html.Div([
        # Gauge for Available Risk
        html.Div([
            html.H3("Available Risk", style={'textAlign': 'center', 'margin-top': '0', 'margin-bottom': '5px'}),
            dcc.Graph(id='available-risk-gauge', config={'displayModeBar': False},
                      style={'height': '180px'}) # Compact height
        ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top', 'padding-right': '10px'}),

        # Progress Bar for Realized P&L
        html.Div([
            html.H3("Realized P&L Progress", style={'textAlign': 'center', 'margin-top': '0', 'margin-bottom': '5px'}),
            html.Div(id='pnl-progress-bar-container', style={'width': '100%'}),
        ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'})
    ], style={'margin-bottom': '20px', 'display': 'flex', 'justify-content': 'space-around', 'align-items': 'flex-start'}),

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
            {"name": "Realized P&L", "id": "Realized P&L", "type": "numeric", "editable": False},
            {"name": "Entry Time", "id": "Entry Time", "editable": False},
            {"name": "Exit Time", "id": "Exit Time", "editable": True},
            {"name": "Trade came to me", "id": "Trade came to me", "presentation": "dropdown"},
            {"name": "With Value", "id": "With Value", "presentation": "dropdown"},
            {"name": "Score", "id": "Score", "presentation": "dropdown"},
            {"name": "Execution", "id": "Execution", "presentation": "dropdown"},
            {"name": "Sizing", "id": "Sizing", "presentation": "dropdown"},
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
                'options': [{'label': i, 'value': i} for i in ['Yes', 'No']],
                'clearable': False
            },\
            'With Value': {
                'options': [{'label': i, 'value': i} for i in ['Yes', 'No']],
                'clearable': False
            },
            'Score': {
                'options': [{'label': i, 'value': i} for i in ['A+', 'A', 'B', 'C', 'D', 'F']],
                'clearable': False
            },
            'Execution': {
                'options': [{'label': i, 'value': i} for i in ['Calm Execution', 'Hesitant', 'Overtrading', 'Revenge Trading']],
                'clearable': False
            },
            'Sizing': {
                'options': [{'label': i, 'value': i} for i in ['Base', 'Increased', 'Reduced']],
                'clearable': False
            },
        },
        style_data_conditional=[
            # Conditional styling for Risk ($) exceeding daily_risk. This rule will be applied first.
            {
                'if': {
                    'filter_query': '{Risk ($)} > ' + str(config['daily_risk'])
                },
                'backgroundColor': '#FF4136', # Red background
                'color': 'white'
            },
            # Conditional row coloring based on Realized P&L.
            # These rules come after the Risk rule, so they take precedence if both apply.
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
        style_cell={ # Default style for all cells
            'textAlign': 'left',
            'padding': '5px',
            'fontFamily': 'sans-serif',
            'minWidth': 80, 'width': 80, 'maxWidth': 180
        },
        style_cell_conditional=[ # Specific widths for certain columns
            {'if': {'column_id': 'Trade #'}, 'minWidth': 80, 'width': 80},
            {'if': {'column_id': 'Futures Type'}, 'minWidth': 120, 'width': 120},
            {'if': {'column_id': 'Size'}, 'minWidth': 80, 'width': 80},
            {'if': {'column_id': 'Stop Loss (pts)'}, 'minWidth': 130, 'width': 130},
            {'if': {'column_id': 'Risk ($)'}, 'minWidth': 100, 'width': 100},
            {'if': {'column_id': 'Status'}, 'minWidth': 100, 'width': 100},
            {'if': {'column_id': 'Points Realized'}, 'minWidth': 130, 'width': 130},
            {'if': {'column_id': 'Realized P&L'}, 'minWidth': 130, 'width': 130},
            {'if': {'column_id': 'Entry Time'}, 'minWidth': 180, 'width': 180},
            {'if': {'column_id': 'Exit Time'}, 'minWidth': 180, 'width': 180},
            {'if': {'column_id': 'Trade came to me'}, 'minWidth': 150, 'width': 150},
            {'if': {'column_id': 'With Value'}, 'minWidth': 120, 'width': 120},
            {'if': {'column_id': 'Score'}, 'minWidth': 80, 'width': 80},
            {'if': {'column_id': 'Execution'}, 'minWidth': 150, 'width': 150},
            {'if': {'column_id': 'Sizing'}, 'minWidth': 100, 'width': 100},
        ],
        style_header={ # Style for header cells
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        css=[{ # General CSS adjustments
            'selector': '.dash-spreadsheet-container .dash-spreadsheet-table',
            'rule': 'font-size: 14px;'
        },
        { # Target the text label within the dropdown for padding adjustment
            'selector': '.dash-cell div.dash-dropdown .Select-value-label',
            'rule': 'padding-right: 25px !important;'
        },
        { # Target the dropdown arrow itself to adjust its position
            'selector': '.dash-cell div.dash-dropdown .Select-arrow',
            'rule': 'right: 5px !important;'
        }
        ]
    ),
    html.Div(id='debug-output', style={'margin-top': '20px', 'color': 'red'})
])

@app.callback(
    Output('trades-table', 'data'),
    Input('add-trade-button', 'n_clicks'),
    State('trades-table', 'data')
)
def add_row(n_clicks, rows):
    """
    Adds a new row to the table with default and calculated values
    when the 'Add Trade' button is clicked.
    """
    if n_clicks > 0:
        if rows is None:
            rows = []

        trade_num = len(rows) + 1

        default_futures_type = config['default_futures_type']
        default_size = config['default_size']
        
        # Ensure 'mf' exists for the default futures type and default_size is valid
        if default_futures_type in config['futures_types'] and default_size is not None and default_size > 0:
            mf = config['futures_types'][default_futures_type]['mf']
            stop_loss_pts = config['daily_risk'] / (default_size * mf)
            risk_dollars = stop_loss_pts * default_size * mf
        else:
            stop_loss_pts = None
            risk_dollars = None
            print("Warning: Could not calculate default Stop Loss/Risk. Check config or default values.")

        new_row = {
            "Trade #": trade_num,
            "Futures Type": default_futures_type,
            "Size": default_size,
            "Stop Loss (pts)": round(stop_loss_pts, 2) if stop_loss_pts is not None else "",
            "Risk ($)": round(risk_dollars, 2) if risk_dollars is not None else "",
            "Status": "Active", # New trades start as Active
            "Points Realized": "",
            "Realized P&L": "",
            "Entry Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Exit Time": "",
            "Trade came to me": "Yes",
            "With Value": "Yes",
            "Score": "A+",
            "Execution": "Calm Execution",
            "Sizing": "Base"
        }
        rows.append(new_row)
    return rows

@app.callback(
    Output('trades-table', 'data', allow_duplicate=True),
    Input('trades-table', 'data'),
    State('trades-table', 'data_previous'),
    prevent_initial_call=True
)
def update_calculated_columns(current_data, previous_data):
    """
    Recalculates 'Risk ($)' and 'Realized P&L' when relevant inputs change,
    and fills 'Exit Time', sets 'Status', and applies row colors based on trade status and P&L.
    """
    if current_data is None or previous_data is None:
        return dash.no_update

    # If data hasn't changed, do nothing
    if current_data == previous_data:
        return dash.no_update

    updated_rows = []
    for i, row in enumerate(current_data):
        is_existing_row = i < len(previous_data) # Check if row existed previously and is not new

        # Get current and previous values for comparison
        status_current = row.get("Status")
        status_previous = previous_data[i].get("Status") if is_existing_row else None
        
        points_realized_current = row.get("Points Realized")
        points_realized_previous = previous_data[i].get("Points Realized") if is_existing_row else None

        # Helper to safely convert to float or None for comparison
        def safe_float(val):
            try:
                return float(val) if val not in [None, ''] else None
            except ValueError:
                return None # Handles cases where non-numeric text might be entered

        points_realized_current_num = safe_float(points_realized_current)
        points_realized_previous_num = safe_float(points_realized_previous)


        # --- Logic for Points Realized entry/deletion ---
        # Scenario 1: Points Realized is entered (was blank/None, now has a value)
        if points_realized_current_num is not None and points_realized_previous_num is None:
            row["Status"] = "Closed"
            if not row.get("Exit Time"): # Only fill if not already filled
                row["Exit Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Scenario 2: Points Realized is deleted (was a value, now blank/None)
        elif points_realized_current_num is None and points_realized_previous_num is not None:
            row["Status"] = "Active"
            row["Realized P&L"] = "" # Blank out Realized P&L
            row["Exit Time"] = ""    # Blank out Exit Time
            # Row color will reset automatically due to P&L being blank

        # --- Recalculate Risk ($) and Realized P&L based on relevant changes ---
        should_recalculate_pnl = False
        # Trigger recalculation if any core input changes, including Status
        # The points_realized change is now handled above for status/exit time,
        # but it still needs to trigger P&L recalculation.
        if (points_realized_current != points_realized_previous or
            status_current != status_previous or # Manual status change
            row.get("Futures Type") != (previous_data[i].get("Futures Type") if is_existing_row else None) or
            row.get("Size") != (previous_data[i].get("Size") if is_existing_row else None) or
            row.get("Stop Loss (pts)") != (previous_data[i].get("Stop Loss (pts)") if is_existing_row else None)):
            should_recalculate_pnl = True
        
        # Also recalculate if it's a brand new row just added
        elif i == len(current_data) - 1 and len(current_data) > len(previous_data):
            should_recalculate_pnl = True

        if should_recalculate_pnl:
            futures_type = row.get("Futures Type")
            size = row.get("Size")
            stop_loss_pts = row.get("Stop Loss (pts)")
            current_points_realized_for_calc = row.get("Points Realized") # Use potentially updated value for P&L calc

            # --- Recalculate Risk ($) ---
            if (futures_type in config['futures_types'] and
                isinstance(size, (int, float)) and size is not None and size > 0 and
                isinstance(stop_loss_pts, (int, float)) and stop_loss_pts is not None):
                mf = config['futures_types'][futures_type]['mf']
                calculated_risk_dollars = size * stop_loss_pts * mf
                row["Risk ($)"] = round(calculated_risk_dollars, 2)
            else:
                row["Risk ($)"] = None

            # --- Recalculate Realized P&L ---
            if (current_points_realized_for_calc not in [None, ''] and
                futures_type in config['futures_types'] and
                isinstance(size, (int, float)) and size is not None and size > 0):
                try:
                    points_realized_num_for_calc = float(current_points_realized_for_calc)
                    mf = config['futures_types'][futures_type]['mf']
                    calculated_pnl = size * points_realized_num_for_calc * mf
                    row["Realized P&L"] = round(calculated_pnl, 2)
                except ValueError:
                    row["Realized P&L"] = None # If user typed invalid text, clear P&L
            else: # If Points Realized is blank/None, ensure Realized P&L is blank
                row["Realized P&L"] = ""
                
        updated_rows.append(row)
    
    return updated_rows

# Callback for Available Risk Gauge
@app.callback(
    Output('available-risk-gauge', 'figure'),
    Input('trades-table', 'data')
)
def update_available_risk_gauge(rows):
    daily_risk_limit = config['daily_risk']

    if not rows:
        available_risk = daily_risk_limit
        active_risk = 0
        realized_pnl = 0
    else:
        df = pd.DataFrame(rows)
        df['Risk ($)'] = pd.to_numeric(df['Risk ($)'], errors='coerce').fillna(0)
        df['Realized P&L'] = pd.to_numeric(df['Realized P&L'], errors='coerce').fillna(0)
        
        active_risk = df[df['Status'] == 'Active']['Risk ($)'].sum()
        realized_pnl = df[df['Status'] == 'Closed']['Realized P&L'].sum()
        
        available_risk = max(0, daily_risk_limit + realized_pnl - active_risk)

    max_range = max(daily_risk_limit * 1.2, available_risk * 1.1)
    if config.get('profit_target') and config['profit_target'] > 0:
        max_range = max(max_range, config['profit_target'] * 1.1)

    steps = [
        {'range': [0, daily_risk_limit * 0.2], 'color': "red"},
        {'range': [daily_risk_limit * 0.2, daily_risk_limit * 0.6], 'color': "orange"},
        {'range': [daily_risk_limit * 0.6, daily_risk_limit], 'color': "yellowgreen"},
        {'range': [daily_risk_limit, max_range], 'color': "green"}
    ]
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = available_risk,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Available Risk", 'font': {'size': 16}},
        gauge = {
            'axis': {'range': [0, max_range], 'tickwidth': 1, 'tickcolor': "darkblue", 'nticks': 5},
            'bar': {'color': "rgba(0,0,0,0)"},
            'steps': steps,
            'threshold': {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.75,
                'value': daily_risk_limit
            }
        }
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="white",
        font={'color': "black", 'family': "Arial"}
    )
    return fig

# Callback for Realized P&L Progress Bar
@app.callback(
    Output('pnl-progress-bar-container', 'children'),
    Input('trades-table', 'data')
)
def update_pnl_progress_bar(rows):
    profit_target = config.get('profit_target', 1)
    total_realized_pnl = 0

    if rows:
        df = pd.DataFrame(rows)
        df['Realized P&L'] = pd.to_numeric(df['Realized P&L'], errors='coerce').fillna(0)
        total_realized_pnl = df['Realized P&L'].sum()

    progress_val = abs(total_realized_pnl)
    
    percent = (progress_val / profit_target) * 100 if profit_target != 0 else 0
    percent = max(min(percent, 100), 0)

    if total_realized_pnl < 0:
        bar_color = "linear-gradient(to right, #ffc1c1, #ff4d4d, #cc0000)" # Red gradient
        text_color = "white"
        pnl_text = f"-${abs(total_realized_pnl):,.2f}"
    else:
        bar_color = "linear-gradient(to right, #e6ffe6, #66cc66, #008000)" # Lighter green -> Darker green
        text_color = "white"
        pnl_text = f"+${total_realized_pnl:,.2f}"

    main_bar_visual_div = html.Div(
        style={
            'background-color': '#e0e0e0',
            'borderRadius': '20px',
            'height': '30px',
            'position': 'relative',
            'overflow': 'hidden',
            'boxShadow': 'inset 0 1px 3px rgba(0,0,0,0.2)'
        },
        children=[
            html.Div(style={
                'background': bar_color,
                'width': f'{percent}%',
                'height': '100%',
                'border-radius': '20px',
                'display': 'flex',
                'align-items': 'center',
                'justify-content': 'center',
                'fontWeight': 'bold',
                'color': text_color,
                'fontSize': '14px',
                'transition': 'width 0.5s ease-in-out'
            }, children=[
                pnl_text
            ]),
            html.Div(
                "🏁",
                style={
                    'position': 'absolute',
                    'right': '6px',
                    'top': '2px',
                    'fontSize': '20px',
                    'zIndex': 2
                }
            ) if profit_target > 0 else None
        ]
    )

    target_display_div = html.Div(
        f"Target: ${profit_target:,.2f}",
        style={
            'textAlign': 'right',
            'fontSize': '12px',
            'color': '#555',
            'marginTop': '2px'
        }
    )

    return [
        main_bar_visual_div,
        target_display_div
    ]


if __name__ == '__main__':
    app.run(debug=True)