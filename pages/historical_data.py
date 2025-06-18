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
                {"name": "DB ID", "id": "id", "type": "numeric", "editable": False},
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
    ], style={'width': '95%', 'margin': '0 auto'}),
    # NEW: Confirmation Dialog and Store for Deletion
    dcc.ConfirmDialog(
        id='confirm-delete-dialog',
        message='Are you sure you want to permanently delete this trade from the database?',
    ),
    dcc.Store(id='trade-id-to-delete', data=None), # To store the ID of the row pending deletion
    html.Div(id='delete-confirmation-message', style={'marginTop': '10px', 'textAlign': 'center', 'fontWeight': 'bold'}) # Feedback message
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

########################################################################
# This callback updates the SQLlite database when edits or deletions are made in the DataTable.
# Update_historical_db_on_edit_delete callback
##############################################################

# Locate this section in pages/historical_data.py:
# @dash.callback(
#     Output('load-db-output-message', 'children', allow_duplicate=True),
#     Output('trade-id-to-delete', 'data'),
#     Output('confirm-delete-dialog', 'displayed', allow_duplicate=True), # Original output
#     Input('historical-trades-table', 'data'),
#     Input('load-all-trades-button', 'n_clicks'),
#     State('historical-trades-table', 'data_previous'),
#     prevent_initial_call=True
# )
# def update_historical_db_on_edit_delete(...):
#     ...

# REPLACE its entire content with this:
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