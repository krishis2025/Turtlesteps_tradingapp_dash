# pages/historical_data.py

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import pandas as pd
import sys
import os
from datetime import datetime
import json
import base64

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
    # Button to load all trades from the database
    # This button will trigger a callback to load data into the DataTable
    # NEW: Add Export JSON Button next to Load All Trades button
    html.Div([
        html.Button("Refresh", id="load-all-trades-button", n_clicks=0,
                    className='dash-button', style={'marginBottom': '10px'}), # Applied class, removed padding/fontSize
        html.Button("Export", id="export-json-button", n_clicks=0,
                    className='dash-button', style={'marginBottom': '10px', 'marginLeft': '10px'}), # Applied class, removed padding/fontSize
        
        
        # NEW: Upload component for importing JSON
        dcc.Upload(
            id='upload-historical-json', # Unique ID for this upload component
            children=html.Div([
                #'Drag and Drop or ',
                html.A('Upload to Database (JSON)', id='upload-historical-json-link') # User-friendly text
            ]),
            style={
                'width': '280px', 'height': '40px', 'lineHeight': '40px',
                'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                'textAlign': 'center', 'margin': '10px 0 10px 10px', 'cursor': 'pointer',
                'display': 'inline-block', 'verticalAlign': 'middle'
            },
            multiple=False # Allow only single file upload
        ),
        html.Div(id='load-db-output-message', style={'marginTop': '10px', 'textAlign': 'left', 'flexBasis': '100%'}) # Message area
    ], style={'width': '95%', 'margin': '0 auto 20px auto', 'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap', 'justifyContent': 'flex-start'}), # Added display:flex and flexWrap for alignment
    
    ##############################################
    #Filter Historical data Html wrapper
    ##############################################
    html.Div([
        html.H3("Filter Historical Data", style={'textAlign': 'center', 'width': '100%', 'marginBottom': '25px'}), # Ensure it spans full width and more margin
        
        # Date Range Picker
        html.Div([
            html.Label("Date Range:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.DatePickerRange(
                id='historical-date-range-picker',
                start_date_placeholder_text="Start Date",
                end_date_placeholder_text="End Date",
                display_format='MM-DD-YYYY',
                month_format='MMMM Y',
                calendar_orientation='horizontal',
                updatemode='bothdates',
                clearable=True, # ADDED: Allows clearing the selected date range
                style={'marginRight': '15px'}
            ),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px', 'flexWrap': 'wrap', 'marginRight': '20px'}), # Increased margin-bottom and added right margin

        # Categorical Dropdowns      
        html.Div([ # Container for all categorical filters - now each dropdown has its own wrapper
            # Futures Type
            html.Div([
                html.Label("Futures Type:", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                dcc.Dropdown(
                    id='historical-filter-futures-type',
                    options=[], # Options loaded by callback
                    placeholder='All', clearable=True, style={'width': '150px'}
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px', 'marginRight': '20px'}), # Consistent spacing

            # Status
            html.Div([
                html.Label("Status:", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                dcc.Dropdown(
                    id='historical-filter-status',
                    options=[{'label': 'Active', 'value': 'Active'}, {'label': 'Closed', 'value': 'Closed'}],
                    placeholder='All', clearable=True, style={'width': '150px'}
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px', 'marginRight': '20px'}),

            # Trade Came To Me
            html.Div([
                html.Label("Trade Came To Me:", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                dcc.Dropdown(
                    id='historical-filter-trade-came',
                    options=[{'label': 'Yes', 'value': 'Yes'}, {'label': 'No', 'value': 'No'}],
                    placeholder='All', clearable=True, style={'width': '150px'}
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px', 'marginRight': '20px'}),

            # With Value
            html.Div([
                html.Label("With Value:", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                dcc.Dropdown(
                    id='historical-filter-with-value',
                    options=[{'label': 'Yes', 'value': 'Yes'}, {'label': 'No', 'value': 'No'}],
                    placeholder='All', clearable=True, style={'width': '150px'}
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px', 'marginRight': '20px'}),

            # Score
            html.Div([
                html.Label("Score:", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                dcc.Dropdown(
                    id='historical-filter-score',
                    options=[{'label': 'A+', 'value': 'A+'}, {'label': 'B', 'value': 'B'}, {'label': 'C', 'value': 'C'}],
                    placeholder='All', clearable=True, style={'width': '100px'}
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px', 'marginRight': '20px'}),

            # Entry Quality
            html.Div([
                html.Label("Entry Quality:", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                dcc.Dropdown(
                    id='historical-filter-entry-quality',
                    options=[
                        {'label': 'Waited Patiently', 'value': 'Waited Patiently'},
                        {'label': 'Calm / Standard', 'value': 'Calm / Standard'},
                        {'label': 'Impulsive / FOMO', 'value': 'Impulsive / FOMO'},
                        {'label': 'Hesitant / Missed', 'value': 'Hesitant / Missed'},
                        {'label': 'Forced / Overtraded', 'value': 'Forced / Overtraded'},
                    ],
                    placeholder='All', clearable=True, style={'width': '200px'}
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px', 'marginRight': '20px'}),

            # Emotional State
            html.Div([
                html.Label("Emotional State:", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                dcc.Dropdown(
                    id='historical-filter-emotional-state',
                    options=[
                        {'label': 'Calm / Disciplined', 'value': 'Calm / Disciplined'},
                        {'label': 'Get back losses', 'value': 'Get back losses'},
                        {'label': 'FOMO', 'value': 'FOMO'},
                        {'label': 'Fear of giving away profit', 'value': 'Fear of giving away profit'},
                        {'label': 'Overconfidence', 'value': 'Overconfidence'},
                        {'label': 'Frustration / Impatience', 'value': 'Frustration / Impatience'},
                        {'label': 'Distracted', 'value': 'Distracted'},
                    ],
                    placeholder='All', clearable=True, style={'width': '200px'}
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px', 'marginRight': '20px'}),

            # Sizing
            html.Div([
                html.Label("Sizing:", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                dcc.Dropdown(
                    id='historical-filter-sizing',
                    options=[{'label': 'Base', 'value': 'Base'}, {'label': 'Increased', 'value': 'Increased'}, {'label': 'Reduced', 'value': 'Reduced'}],
                    placeholder='All', clearable=True, style={'width': '150px'}
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px', 'marginRight': '20px'}),

            # Show Columns (already has its own specific styling)
            html.Div([
                html.Label("Show Columns:", style={'fontWeight': 'bold', 'marginRight': '5px'}),
                dcc.Dropdown(
                    id='column-visibility-filter',
                    options=[], # Will be populated by a callback
                    value=[], # Default to showing all initially, will be dynamically set
                    multi=True, # Allows selecting multiple columns
                    placeholder='Select columns to show', clearable=False, style={'minWidth': '200px', 'flexGrow': 1}
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'flexGrow': 1}), # Remaining style from before

        ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'flex-start', 'width': '100%'}), # Parent for all filter groups
    ], style={
            'width': '95%',
            'margin': '0 auto 20px auto',
            'padding': '25px', # Increased padding for more breathing room
            'backgroundColor': '#ffffff', # White background for the filter block
            'borderRadius': '8px',
            'boxShadow': '0 2px 10px rgba(0, 0, 0, 0.08)', # Consistent shadow
            'display': 'flex', # Added flex to manage internal layout more precisely
            'flexWrap': 'wrap', # Allow filter groups to wrap
            'alignItems': 'flex-start', # Align items to the top
            'justifyContent': 'space-between' # Distribute space between filter groups
        }), 
    

    ####################################################################################
    #Data table to display historical data
    ##############################################################################
    # DataTable to display historical data
    html.Div([
        dash_table.DataTable(
            id='historical-trades-table', # Unique ID for this table
            columns=[
                {"name": "DB ID", "id": "id", "type": "numeric", "editable": False, "hideable": True}, # ADDED hideable: True
                {"name": "Trade #", "id": "Trade #", "type": "numeric", "editable": False, "hideable": True}, # ADDED hideable: True
                {"name": "Futures Type", "id": "Futures Type", "presentation": "dropdown", "hideable": True}, # ADDED hideable: True
                {"name": "Size", "id": "Size", "type": "numeric", "editable": True, "hideable": True}, # ADDED hideable: True
                {"name": "Stop Loss (pts)", "id": "Stop Loss (pts)", "type": "numeric", "editable": True, "hideable": True}, # ADDED hideable: True
                {"name": "Risk ($)", "id": "Risk ($)", "type": "numeric", "editable": False, "hideable": True}, # ADDED hideable: True
                {"name": "Status", "id": "Status", "presentation": "dropdown", "editable": True, "hideable": True}, # ADDED hideable: True
                {"name": "Points Realized", "id": "Points Realized", "type": "numeric", "editable": True, "hideable": True}, # ADDED hideable: True
                {"name": "Realized P&L", "id": "Realized P&L", "type": "numeric", "editable": False, "format": {"specifier": ".2f"}, "hideable": True}, # ADDED hideable: True
                {"name": "Entry Time", "id": "Entry Time", "editable": False, "hideable": True}, # ADDED hideable: True
                {"name": "Exit Time", "id": "Exit Time", "editable": True, "hideable": True}, # ADDED hideable: True
                {"name": "Trade came to me", "id": "Trade came to me", "presentation": "dropdown", "hideable": True}, # ADDED hideable: True
                {"name": "With Value", "id": "With Value", "presentation": "dropdown", "hideable": True}, # ADDED hideable: True
                {"name": "Score", "id": "Score", "presentation": "dropdown", "hideable": True}, # ADDED hideable: True
                {"name": "Entry Quality", "id": "Entry Quality", "presentation": "dropdown", "hideable": True}, # ADDED hideable: True
                {"name": "Emotional State", "id": "Emotional State", "presentation": "dropdown", "hideable": True}, # ADDED hideable: True
                {"name": "Sizing", "id": "Sizing", "presentation": "dropdown", "hideable": True}, # ADDED hideable: True
                {"name": "Notes", "id": "Notes", "type": "text", "editable": True, "hideable": True}, # ADDED hideable: True
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
    ], style={'width': '95%', 'margin': '0 auto'}),
    # NEW: Download component for JSON export
    dcc.Download(id="download-historical-json"), 
    # NEW: Confirmation Dialog and Store for Deletion
    dcc.ConfirmDialog(
        id='confirm-delete-dialog',
        message='Are you sure you want to permanently delete this trade from the database?',
    ),
    dcc.Store(id='trade-id-to-delete', data=None), # To store the ID of the row pending deletion
    html.Div(id='delete-confirmation-message', style={'marginTop': '10px', 'textAlign': 'center', 'fontWeight': 'bold'}), # Feedback message  
        
    # NEW: Interval for initial data load on page access
    dcc.Interval(id='historical-load-interval', interval=1000, n_intervals=0, max_intervals=1), # Triggers once after 1 second
    # NEW: Store to hold all raw historical data after initial load
    dcc.Store(id='historical-trades-table-data-store', data=[]),    
])  


# --- Callbacks for the Historical Data Page ---
##########################################################################
# Load All Trades from Database into DataTable callback
################################################################

@dash.callback(
    Output('historical-trades-table-data-store', 'data'), # CHANGED: Output to dcc.Store
    Output('load-db-output-message', 'children'),
    Input('load-all-trades-button', 'n_clicks'),
    Input('historical-load-interval', 'n_intervals'),
    prevent_initial_call=True
)
def load_all_trades_into_table(n_clicks_button, n_intervals_interval):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'initial_load'

    if trigger_id == 'historical-load-interval' or trigger_id == 'load-all-trades-button':
        try:
            db.initialize_db()
            all_trades_raw = db.fetch_all_trades_from_db()
            
            df_all_trades = pd.DataFrame(all_trades_raw)
            if not df_all_trades.empty and 'Entry Time' in df_all_trades.columns:
                df_all_trades['Entry Time'] = pd.to_datetime(df_all_trades['Entry Time'], errors='coerce')
                df_all_trades = df_all_trades.sort_values(by='Entry Time', ascending=False)
                all_trades_final = df_all_trades.to_dict('records')
            else:
                all_trades_final = []

            db_name, table_name = db.get_database_info()
            
            message = html.Div([
                html.P(f"Loaded {len(all_trades_final)} trades from database '{db_name}' table '{table_name}'.", style={'color': 'green'}),
                html.P("Table is editable and changes are synced to DB. Use the button to refresh.", style={'color': 'gray', 'fontSize': '12px'})
            ])
            return all_trades_final, message # Returns data to store
        except Exception as e:
            db_name, table_name = db.get_database_info()
            message = html.Div([
                html.P(f"Error loading trades from database '{db_name}' table '{table_name}': {e}", style={'color': 'red'}),
                html.P("Please ensure database file exists and is accessible.", style={'color': 'gray', 'fontSize': '12px'})
            ])
            return [], message # Returns empty data to store on error
    return dash.no_update, ""


########################################################################
# NEW CALLBACK: For Export All Trades (JSON) Button
# This callback exports all historical trades to a JSON file when the button is clicked.
########################################################################

@dash.callback(
    Output("download-historical-json", "data"),
    Input("export-json-button", "n_clicks"),
    prevent_initial_call=True,
)
def export_all_trades_json(n_clicks):
    if n_clicks:
        try:
            db_name, table_name = db.get_database_info()
            all_trades = db.fetch_all_trades_from_db() # Fetch all data
            
            if not all_trades:
                # Optionally return a notification if there's no data to export
                return dash.no_update # Or send a dummy file indicating no data

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"allData_{db_name.replace('.db', '')}_{timestamp}.json"
            
            # Convert list of dicts directly to JSON string
            json_string = json.dumps(all_trades, indent=2) # indent for readability

            return dcc.send_string(json_string, filename)
        except Exception as e:
            print(f"Error exporting trades to JSON: {e}")
            # In a real app, you might output an error message to the page
            return dash.no_update
    return dash.no_update

########################################################################
# NEW CALLBACK: For Importing Trades from JSON File via Upload
##################################################################

# REPLACE its entire content with this:
@dash.callback(
    Output('historical-trades-table', 'data', allow_duplicate=True), # Output to refresh the table
    Output('load-db-output-message', 'children', allow_duplicate=True), # Message for import status
    Input('upload-historical-json', 'contents'), # Trigger when a file is uploaded
    State('upload-historical-json', 'filename'), # Get the filename
    prevent_initial_call=True
)
def import_trades_json(contents, filename):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded_content = base64.b64decode(content_string)

        try:
            if filename and filename.endswith('.json'):
                loaded_data = json.loads(decoded_content.decode('utf-8'))
                
                if not isinstance(loaded_data, list):
                    return dash.no_update, html.Div("Error: Imported file is not a valid list of trades.", style={'color': 'red'})

                imported_count = 0
                error_count = 0
                for row_data in loaded_data:
                    # NEW: Use upsert_trade_to_db to insert new records or modify existing ones
                    # We pass the 'id' if it exists in row_data, to allow updates
                    upserted_id = db.upsert_trade_to_db(row_data) 
                    if upserted_id is not None:
                        imported_count += 1
                        # Update the 'id' in row_data in case it was a new insert (for table refresh)
                        row_data['id'] = upserted_id 
                    else:
                        error_count += 1
                
                # After saving all, fetch all data from DB to refresh the table with current state
                refreshed_data = db.fetch_all_trades_from_db()
                message_text = f"Successfully imported {imported_count} trades from '{filename}'."
                if error_count > 0:
                    message_text += f" ({error_count} trades failed to import)."
                
                return refreshed_data, html.Div(message_text, style={'color': 'green' if error_count == 0 else 'orange'})
            else:
                return dash.no_update, html.Div("Error: Please upload a .json file.", style={'color': 'red'})
        except json.JSONDecodeError:
            return dash.no_update, html.Div("Error: Invalid JSON file content.", style={'color': 'red'})
        except Exception as e:
            print(f"Error importing trades from JSON file {filename}: {e}")
            return dash.no_update, html.Div(f"Error processing file: {e}", style={'color': 'red'})
    return dash.no_update, dash.no_update

###################################################################################
# NEW CALLBACK: Filter Historical Data Table based on inputs
#########################################################################
@dash.callback(
    Output('historical-trades-table', 'data'), # Output to update the DataTable
    Output('historical-filter-futures-type', 'options'), # NEW: Output to populate Futures Type dropdown options
    Input('historical-trades-table-data-store', 'data'), # Get all raw data from the store
    Input('historical-date-range-picker', 'start_date'),
    Input('historical-date-range-picker', 'end_date'),
    Input('historical-filter-futures-type', 'value'),
    Input('historical-filter-status', 'value'),
    Input('historical-filter-trade-came', 'value'),
    Input('historical-filter-with-value', 'value'),
    Input('historical-filter-score', 'value'),
    Input('historical-filter-entry-quality', 'value'),
    Input('historical-filter-emotional-state', 'value'),
    Input('historical-filter-sizing', 'value'),
    prevent_initial_call=False # Allow to run on initial load to populate default view
)
def filter_historical_data_table(all_historical_data, start_date, end_date, 
                                 futures_type_val, status_val, trade_came_val, 
                                 with_value_val, score_val, entry_quality_val, 
                                 emotional_state_val, sizing_val):
    if not all_historical_data:
        # Return empty data and empty options if no historical data is loaded
        return [], []

    df = pd.DataFrame(all_historical_data)

    # Convert relevant columns to correct dtypes for filtering
    df['Entry Time'] = pd.to_datetime(df['Entry Time'], errors='coerce')
    df['Realized P&L'] = pd.to_numeric(df['Realized P&L'], errors='coerce')

    # --- Populate Futures Type Dropdown Options ---
    futures_type_options = [{'label': i, 'value': i} for i in sorted(df['Futures Type'].dropna().unique())]

    # --- Apply Filters ---
    df_filtered = df.copy()

    # Date Range Filter
    if start_date and end_date:
        start_datetime = pd.to_datetime(start_date).date()
        end_datetime = pd.to_datetime(end_date).date()
        df_filtered = df_filtered[(df_filtered['Entry Time'].dt.date >= start_datetime) & (df_filtered['Entry Time'].dt.date <= end_datetime)]

    # Categorical Filters
    if futures_type_val:
        df_filtered = df_filtered[df_filtered['Futures Type'] == futures_type_val]
    if status_val:
        df_filtered = df_filtered[df_filtered['Status'] == status_val]
    if trade_came_val:
        df_filtered = df_filtered[df_filtered['Trade came to me'] == trade_came_val]
    if with_value_val:
        df_filtered = df_filtered[df_filtered['With Value'] == with_value_val]
    if score_val:
        df_filtered = df_filtered[df_filtered['Score'] == score_val]
    if entry_quality_val:
        df_filtered = df_filtered[df_filtered['Entry Quality'] == entry_quality_val]
    if emotional_state_val:
        df_filtered = df_filtered[df_filtered['Emotional State'] == emotional_state_val]
    if sizing_val:
        df_filtered = df_filtered[df_filtered['Sizing'] == sizing_val]

    # Return filtered data and dropdown options
    return df_filtered.to_dict('records'), futures_type_options

########################################################################
# This callback updates the SQLlite database when edits or deletions are made in the DataTable.
# Update_historical_db_on_edit_delete callback
##############################################################

@dash.callback(
    Output('load-db-output-message', 'children', allow_duplicate=True),
    Output('trade-id-to-delete', 'data'), # This output sends ID to the dcc.Store
    Input('historical-trades-table', 'data'),
    Input('load-all-trades-button', 'n_clicks'),
    State('historical-trades-table', 'data_previous'),
    prevent_initial_call=True
)
def update_historical_db_on_edit_delete(current_data, load_btn_n_clicks, previous_data):
    ctx = dash.callback_context

    message = dash.no_update
    trade_id_to_delete_output = dash.no_update # Default: no ID to signal for deletion

    # If the trigger was specifically the 'Load All Trades' button, do nothing with deletion logic
    if ctx.triggered_id == 'load-all-trades-button':
        return message, trade_id_to_delete_output # Return default no_update for message and ID

    if previous_data is None:
        return dash.no_update, dash.no_update

    if current_data == previous_data:
        return dash.no_update, dash.no_update

    previous_id_map = {row.get('id'): row for row in previous_data if 'id' in row and row.get('id') is not None}
    current_id_map = {row.get('id'): row for row in current_data if 'id' in row and row.get('id') is not None}

    # --- Detect DELETED rows ---
    if len(current_data) < len(previous_data):
        deleted_db_ids = []
        for db_id, row_data in previous_id_map.items():
            if db_id not in current_id_map:
                deleted_db_ids.append(db_id)

        if deleted_db_ids:
            first_deleted_id = deleted_db_ids[0] 

            trade_id_to_delete_output = first_deleted_id # Store the ID of the trade to delete
            message = html.Div(f"Confirm deletion of Trade (DB ID: {first_deleted_id})...", style={'color': 'orange'})

            return message, trade_id_to_delete_output # This triggers the show_delete_confirm_dialog

    # --- Detect MODIFIED rows (and potentially newly pasted rows if they have no 'id') ---
    for current_row_data in current_data:
        current_row_db_id = current_row_data.get('id')
        previous_row_data = previous_id_map.get(current_row_db_id, {}) 

        modified_or_new_row_detected = False
        if current_row_data != previous_row_data:
             modified_or_new_row_detected = True
        elif current_row_db_id is None or current_row_db_id not in previous_id_map:
             modified_or_new_row_detected = True

        if modified_or_new_row_detected:
            row_copy = current_row_data.copy() 

            if row_copy.get('id') is None or row_copy.get('id') not in previous_id_map:
                try:
                    new_db_id = db.save_trade_to_db(row_copy)
                    if new_db_id is not None:
                        row_copy['id'] = new_db_id
                        message = html.Div(f"Pasted new trade (DB ID: {new_db_id}).", style={'color': 'green'})
                    else:
                        message = html.Div(f"Failed to save pasted trade.", style={'color': 'red'})
                except Exception as e:
                    print(f"Error saving pasted historical trade to DB: {e}")
                    message = html.Div(f"Error saving pasted trade. {e}", style={'color': 'red'})
            else:
                try:
                    db.update_trade_in_db(row_copy['id'], row_copy)
                    message = html.Div(f"Updated trade (DB ID: {row_copy.get('id')}).", style={'color': 'green'})
                except Exception as e:
                    print(f"Error updating historical trade (DB ID: {row_copy.get('id')}) in DB: {e}")
                    message = html.Div(f"Error updating trade (DB ID: {row_copy.get('id')}). {e}", style={'color': 'red'})

    if message != dash.no_update: # Only return message if there was a save/update activity
        return message, dash.no_update # Return message, no_update for ID

    return dash.no_update, dash.no_update # Default: no message, no ID to delete

############################################################
# NEW CALLBACK: Handle Confirmation Dialog for Deletion
# confirm_delete_and_delete_from_db callback 
##############################################################


@dash.callback(
    Output('historical-trades-table', 'data', allow_duplicate=True),
    Output('delete-confirmation-message', 'children', allow_duplicate=True),
    Output('confirm-delete-dialog', 'displayed'), # NO allow_duplicate=True here - this is the sole controller
    Output('trade-id-to-delete', 'data', allow_duplicate=True), # This is used by update_historical_db_on_edit_delete to trigger dialog
    Input('confirm-delete-dialog', 'submit_n_clicks'), # Trigger when user clicks OK/Cancel in dialog
    State('trade-id-to-delete', 'data'),              # Get the ID of the trade pending deletion
    prevent_initial_call=True
)
def confirm_delete_and_delete_from_db(submit_n_clicks, trade_id_to_delete):
    # Initialize outputs
    refreshed_data = dash.no_update
    message_content = dash.no_update
    close_dialog = False # Default: dialog should close or stay closed
    clear_trade_id_store = dash.no_update # Default: no change to store

    if submit_n_clicks: # This means user clicked 'OK' on the dialog
        if trade_id_to_delete is not None:
            try:
                db.delete_trade_from_db(trade_id_to_delete) # Perform deletion
                message_content = html.Div(f"Trade (DB ID: {trade_id_to_delete}) permanently deleted.", style={'color': 'green'})
                refreshed_data = db.fetch_all_trades_from_db() # Refresh table
                print(f"Trade with DB ID {trade_id_to_delete} permanently deleted from DB.")
                clear_trade_id_store = None # Clear the store on successful deletion
                close_dialog = False # Explicitly close dialog
            except Exception as e:
                message_content = html.Div(f"Error deleting trade (DB ID: {trade_id_to_delete}): {e}", style={'color': 'red'})
                refreshed_data = dash.no_update # Don't update table if error
                print(f"Error deleting trade (DB ID: {trade_id_to_delete}): {e}")
                close_dialog = True # Keep dialog open if error, user might need to re-try
                clear_trade_id_store = dash.no_update # Don't clear store if error
        else: # Clicked OK, but no ID was in store (edge case)
            close_dialog = False
            clear_trade_id_store = None # Clear it just in case
            message_content = html.Div("No trade selected for deletion.", style={'color': 'orange'})

    return refreshed_data, message_content, close_dialog, clear_trade_id_store

########################################################################
# NEW CALLBACK: Show Delete Confirmation Dialog when trade_id_to_delete is set
# confirm_delete_dialog callback
########################################################################
@dash.callback(
    Output('confirm-delete-dialog', 'displayed', allow_duplicate=True),
    Input('trade-id-to-delete', 'data'), # This input gets data from update_historical_db_on_edit_delete
    prevent_initial_call=True
)
def show_delete_confirm_dialog(trade_id_to_delete):
    if trade_id_to_delete is not None:
        return True # Show the dialog
    return False # Keep dialog closed if data is None (e.g. after deletion confirmed)