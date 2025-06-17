# pages/config.py

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html
import json
import os # To get the absolute path for config.json

# --- Page Registration ---
dash.register_page(
    __name__,
    path='/settings',  # URL path for the settings page
    name='Settings',   # Name for navigation link
    title='Trading Dashboard - Settings',
    description='Configure dashboard settings and database name.'
)

# --- Function to load config (will be called in callbacks) ---
def load_config():
    # Construct the path to config.json relative to the app's root
    # assuming config.json is in the same directory as app.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..') # Go up one level from 'pages'
    config_path = os.path.join(project_root, 'config.json')

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: config.json not found at {config_path}. Using default settings.")
        return {
            "daily_risk": 550,
            "profit_target": 600,
            "max_trades_per_day": 6,
            "default_futures_type": "MES",
            "default_size": 5,
            "futures_types": {"ES": { "mf": 50 }, "MES": { "mf": 5 }},
            "pressing_sequence_multipliers": [1, 2, 1.5, 3],
            "database_name": "trades.db" # Default database name
        }

# --- Layout for the Config Page ---
layout = html.Div([
    html.H2("Dashboard Settings", style={'textAlign': 'center', 'marginBottom': '20px'}),
    html.Div([
        html.H3("General Settings", style={'marginBottom': '10px'}),
        html.Div([
            html.Label("Database Name (.db):", style={'fontWeight': 'bold', 'marginRight': '10px', 'minWidth': '150px'}),
            dcc.Dropdown( # CHANGED TO DROPDOWN
                id='config-db-name',
                options=[
                    {'label': 'trades.db (Live Data)', 'value': 'trades.db'},
                    {'label': 'sandbox_trades.db (Test Data)', 'value': 'sandbox_trades.db'}
                ],
                value='trades.db', # Default to live data
                clearable=False,
                style={'flexGrow': 1, 'maxWidth': '300px'}
            ),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),

        html.Div([
            html.Label("Daily Risk ($):", style={'fontWeight': 'bold', 'marginRight': '10px', 'minWidth': '150px'}),
            dcc.Input(id='config-daily-risk', type='number', min=0, step=1, style={'flexGrow': 1, 'maxWidth': '300px'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),

        html.Div([
            html.Label("Profit Target ($):", style={'fontWeight': 'bold', 'marginRight': '10px', 'minWidth': '150px'}),
            dcc.Input(id='config-profit-target', type='number', min=0, step=1, style={'flexGrow': 1, 'maxWidth': '300px'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),

        html.Div([
            html.Label("Max Trades Per Day:", style={'fontWeight': 'bold', 'marginRight': '10px', 'minWidth': '150px'}),
            dcc.Input(id='config-max-trades', type='number', min=1, step=1, style={'flexGrow': 1, 'maxWidth': '300px'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),

        html.Div([
            html.Label("Pressing Multipliers (comma-separated):", style={'fontWeight': 'bold', 'marginRight': '10px', 'minWidth': '150px'}),
            dcc.Input(id='config-pressing-multipliers', type='text', style={'flexGrow': 1, 'maxWidth': '300px'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),

        html.Button('Save Settings', id='save-settings-button', n_clicks=0,
                    style={'padding': '10px 20px', 'fontSize': '16px', 'cursor': 'pointer', 'display': 'block', 'margin': '0 auto'}),
        
        html.Div(id='config-save-output', style={'marginTop': '15px', 'textAlign': 'center', 'fontWeight': 'bold'}),

    ], style={'border': '1px solid #ddd', 'borderRadius': '5px', 'padding': '20px', 'maxWidth': '600px', 'margin': '0 auto'}), # Centered container

    # Hidden interval component to trigger initial load of settings
    dcc.Interval(id='config-interval', interval=1000, n_intervals=0, max_intervals=1),
])

# --- Callbacks for the Config Page ---

@dash.callback(
    [Output('config-db-name', 'value'),
     Output('config-daily-risk', 'value'),
     Output('config-profit-target', 'value'),
     Output('config-max-trades', 'value'),
     Output('config-pressing-multipliers', 'value')],
    Input('config-interval', 'n_intervals') # Trigger on initial page load
)
def load_current_settings(n_intervals):
    if n_intervals > 0:
        config_data = load_config()
        return [
            config_data.get('database_name', 'trades.db'), # Value for the dropdown
            config_data.get('daily_risk', 550),
            config_data.get('profit_target', 600),
            config_data.get('max_trades_per_day', 6),
            ", ".join(map(str, config_data.get('pressing_sequence_multipliers', [1, 2, 1.5, 3])))
        ]
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@dash.callback(
    Output('config-save-output', 'children'),
    Input('save-settings-button', 'n_clicks'),
    State('config-db-name', 'value'), # Input is now from Dropdown
    State('config-daily-risk', 'value'),
    State('config-profit-target', 'value'),
    State('config-max-trades', 'value'),
    State('config-pressing-multipliers', 'value'),
    prevent_initial_call=True
)
def save_settings(n_clicks, db_name, daily_risk, profit_target, max_trades, pressing_multipliers_str):
    if n_clicks > 0:
        try:
            new_config = load_config()
            
            # The db_name is now directly the value from the dropdown
            new_config['database_name'] = db_name if db_name else "trades.db"
            new_config['daily_risk'] = int(daily_risk) if daily_risk is not None else 550
            new_config['profit_target'] = int(profit_target) if profit_target is not None else 600
            new_config['max_trades_per_day'] = int(max_trades) if max_trades is not None else 6
            
            if pressing_multipliers_str:
                new_config['pressing_sequence_multipliers'] = [float(x.strip()) for x in pressing_multipliers_str.split(',') if x.strip()]
            else:
                new_config['pressing_sequence_multipliers'] = [1, 2, 1.5, 3]

            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, '..')
            config_path = os.path.join(project_root, 'config.json')

            with open(config_path, 'w') as f:
                json.dump(new_config, f, indent=2)
            
            return html.Div("Settings saved successfully! Refresh page to apply database changes.", style={'color': 'green'})
        except Exception as e:
            return html.Div(f"Error saving settings: {e}", style={'color': 'red'})
    return ""