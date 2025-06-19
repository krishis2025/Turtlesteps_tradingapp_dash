# utils/database.py - COMPLETE CODE FOR DB HANDLING

import sqlite3
import pandas as pd
import json
from datetime import datetime
import os

# --- Load config to get database name ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..')
config_path = os.path.join(project_root, 'config.json')
try:
    with open(config_path, 'r') as f:
        app_config = json.load(f)
except FileNotFoundError:
    print(f"Error: config.json not found at {config_path}. Using default database name 'trades.db'.")
    app_config = {}

DATABASE_NAME = app_config.get('database_name', 'trades.db')
TABLE_NAME = 'trades_journal'

# --- Define a helper to get the current DB name from config ---
# This helper will be called dynamically by connection functions
def _get_current_db_name():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    config_path = os.path.join(project_root, 'config.json')
    
    current_app_config = {}
    try:
        with open(config_path, 'r') as f:
            current_app_config = json.load(f)
    except FileNotFoundError:
        print(f"Error: config.json not found at {config_path}. Using default database name 'trades.db' for connection.")
    
    return current_app_config.get('database_name', 'trades.db')


# Now, modify get_db_connection() and initialize_db() to use _get_current_db_name()

# Locate get_db_connection() function:
def get_db_connection():
    """Establishes a connection to the SQLite database, dynamically getting the name from config."""
    current_db_name = _get_current_db_name() # Dynamically get the latest DB name
    conn = sqlite3.connect(current_db_name)
    conn.row_factory = sqlite3.Row
    return conn

# Locate initialize_db() function:
def initialize_db():
    """
    Creates the trades_journal table if it doesn't exist in the currently configured database.
    This function now uses the dynamically loaded DB name.
    """
    conn = get_db_connection() # This will now get the latest DB name
    cursor = conn.cursor()

    # ... (rest of initialize_db - CREATE TABLE IF NOT EXISTS logic) ...
    # You might want to update the print statement here to show the dynamic name
    print(f"Database '{_get_current_db_name()}' and table '{TABLE_NAME}' initialized (if not already existing).")

# List of all columns in the DataTable that we want to store and retrieve.
# IMPORTANT: 'id' is the internal SQLite PRIMARY KEY.
COLUMNS_TO_STORE = [
    "Trade #", "Futures Type", "Size", "Stop Loss (pts)", "Risk ($)", "Status",
    "Points Realized", "Realized P&L", "Entry Time", "Exit Time",
    "Trade came to me", "With Value", "Score", "Entry Quality",
    "Emotional State", "Sizing", "Notes"
]

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

# Locate this section in utils/database.py:
# def initialize_db():
#     """Creates the trades_journal table if it doesn't exist."""
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     # ... rest of initialize_db ...
#     print(f"Database '{_get_current_db_name()}' and table '{TABLE_NAME}' initialized (if not already existing).")


# REPLACE its entire content with this:
def initialize_db():
    """
    Creates the trades_journal table if it doesn't exist,
    and adds any new columns defined in COLUMNS_TO_STORE.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current table info to check for existing columns
    cursor.execute(f"PRAGMA table_info({TABLE_NAME});")
    existing_columns_info = cursor.fetchall()
    existing_column_names = [col[1] for col in existing_columns_info] # col[1] is the name

    # Define columns with appropriate SQLite types for initial creation
    column_definitions = []
    for col in COLUMNS_TO_STORE:
        if col in ["Trade #", "Size", "Stop Loss (pts)", "Risk ($)", "Points Realized", "Realized P&L"]:
            column_definitions.append(f"\"{col}\" REAL") # Use REAL for numbers (floats/integers)
        else:
            column_definitions.append(f"\"{col}\" TEXT") # Use TEXT for strings/dropdowns

    # 1. Create table if it doesn't exist
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {', '.join(column_definitions)}
    );
    """
    cursor.execute(create_table_sql)
    conn.commit()
    print(f"Database '{_get_current_db_name()}' and table '{TABLE_NAME}' ensured.")

    # 2. Add new columns to existing table if they are in COLUMNS_TO_STORE but not in DB
    for col in COLUMNS_TO_STORE:
        if col not in existing_column_names:
            column_type = "REAL" if col in ["Trade #", "Size", "Stop Loss (pts)", "Risk ($)", "Points Realized", "Realized P&L"] else "TEXT"
            alter_table_sql = f"ALTER TABLE {TABLE_NAME} ADD COLUMN \"{col}\" {column_type};"
            try:
                cursor.execute(alter_table_sql)
                conn.commit()
                print(f"Added new column '{col}' to table '{TABLE_NAME}'.")
            except sqlite3.Error as e:
                # This can happen if column was added between checks or other issues
                print(f"Warning: Could not add column '{col}' to table '{TABLE_NAME}': {e}")
                conn.rollback() # Rollback if alter failed
    conn.close()



def save_trade_to_db(trade_data_row):
    """
    Saves a single trade (row) to the database.
    Returns the SQLite-generated primary key (id) for the new row.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Filter trade_data_row to only include columns we want to store
    # Ensure keys match COLUMNS_TO_STORE
    filtered_data = {col: trade_data_row.get(col) for col in COLUMNS_TO_STORE}

    columns = ', '.join(f"\"{col}\"" for col in filtered_data.keys())
    placeholders = ', '.join('?' * len(filtered_data))
    values = tuple(filtered_data.values())

    insert_sql = f"INSERT INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})"
    
    try:
        cursor.execute(insert_sql, values)
        conn.commit()
        last_row_id = cursor.lastrowid # Get the auto-generated ID
        # print(f"Trade saved to DB with id: {last_row_id}")
        return last_row_id # Return the new DB ID
    except sqlite3.Error as e:
        print(f"Error saving trade to DB: {e}")
        conn.rollback()
        return None # Return None on failure
    finally:
        conn.close()

#######################################################################################
# Function to Upsert Trade data - handle both insert and update operations
# This function will insert a new trade or update an existing one based on the 'id'
# If 'id' is provided and matches an existing record, it will update that record.
# If 'id' is not provided or does not match, it will insert a new record
########################################################################################
def upsert_trade_to_db(trade_data_row):
    """
    Inserts a new trade or replaces an existing one based on the 'id' (primary key).
    If trade_data_row has an 'id' and it matches an existing record, that record is replaced.
    If no 'id' or 'id' does not match, a new record is inserted.
    Returns the SQLite-generated primary key (id) for the upserted row.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all column names including 'id' for the INSERT OR REPLACE statement
    # Ensure data has all required columns, even if None
    all_columns_in_db = ["id"] + COLUMNS_TO_STORE # COLUMNS_TO_STORE does NOT include 'id'

    # Prepare data for upsert:
    # Use .get() to safely retrieve values, default to None if missing
    # This also ensures we pass the 'id' from row_data if it exists, for REPLACE functionality
    filtered_data = {col: trade_data_row.get(col) for col in all_columns_in_db}
    
    # Exclude 'id' from columns_str and placeholders_str if it's a new insert where id will be AUTOINCREMENTED
    # If trade_data_row has an id, we'll include it in the INSERT OR REPLACE
    # Otherwise, we let AUTOINCREMENT handle it.
    if 'id' in trade_data_row and trade_data_row['id'] is not None:
        columns_to_insert = ', '.join(f"\"{col}\"" for col in all_columns_in_db)
        placeholders = ', '.join('?' * len(all_columns_in_db))
        values = tuple(filtered_data.values())
        upsert_sql = f"INSERT OR REPLACE INTO {TABLE_NAME} ({columns_to_insert}) VALUES ({placeholders})"
    else:
        # If no 'id' is provided, we treat it as a new insert and let AUTOINCREMENT provide the ID
        columns_to_insert_no_id = ', '.join(f"\"{col}\"" for col in COLUMNS_TO_STORE)
        placeholders_no_id = ', '.join('?' * len(COLUMNS_TO_STORE))
        values_no_id = tuple(trade_data_row.get(col) for col in COLUMNS_TO_STORE) # Only values for COLUMNS_TO_STORE
        upsert_sql = f"INSERT INTO {TABLE_NAME} ({columns_to_insert_no_id}) VALUES ({placeholders_no_id})"
    
    try:
        cursor.execute(upsert_sql, values if ('id' in trade_data_row and trade_data_row['id'] is not None) else values_no_id)
        conn.commit()
        
        # Get the ID of the row that was just inserted/replaced
        result_id = trade_data_row['id'] if ('id' in trade_data_row and trade_data_row['id'] is not None) else cursor.lastrowid
        # print(f"Trade upserted to DB with ID: {result_id}")
        return result_id # Return the ID (new or existing)
    except sqlite3.Error as e:
        print(f"Error upserting trade to DB: {e}")
        conn.rollback()
        return None # Return None on failure
    finally:
        conn.close()

def fetch_all_trades_from_db():
    """Fetches all trades from the database as a list of dictionaries, including their internal 'id'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Select all columns, including 'id'
    cursor.execute(f"SELECT id, {', '.join(f'\"{col}\"' for col in COLUMNS_TO_STORE)} FROM {TABLE_NAME} ORDER BY \"Entry Time\" ASC")
    rows = cursor.fetchall()
    conn.close()

    trades = []
    for row in rows:
        trade_dict = {}
        trade_dict['id'] = row['id'] # Include the internal DB ID
        for col_name in COLUMNS_TO_STORE:
            trade_dict[col_name] = row[col_name]
        trades.append(trade_dict)
    return trades



def fetch_trades_by_date(target_date):
    """
    Fetches trades from the database for a specific date.
    target_date should be a datetime.date object.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Convert target_date to string format matching Entry Time in DB
    date_str = target_date.strftime("%Y-%m-%d") # Format for comparison

    # Use LIKE for partial match on date part, assuming Entry Time stores %Y-%m-%d %H:%M:%S
    # Or, if we ensured consistency, we could use date() function of SQLite
    # For robustness, let's use LIKE on the date part
    cursor.execute(
        f"SELECT id, {', '.join(f'\"{col}\"' for col in COLUMNS_TO_STORE)} FROM {TABLE_NAME} WHERE \"Entry Time\" LIKE ? ORDER BY \"Entry Time\" ASC",
        (f"{date_str}%",) # Match YYYY-MM-DD at the beginning of Entry Time string
    )
    rows = cursor.fetchall()
    conn.close()

    trades = []
    for row in rows:
        trade_dict = {}
        trade_dict['id'] = row['id']
        for col_name in COLUMNS_TO_STORE:
            trade_dict[col_name] = row[col_name]
        trades.append(trade_dict)
    return trades

def update_trade_in_db(internal_db_id, new_data):
    """
    Updates an existing trade in the database using its internal 'id'.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    set_clauses = []
    values = []
    for col_name, value in new_data.items():
        if col_name not in ["id", "Trade #"]: # Don't update internal 'id' or user-facing 'Trade #'
            set_clauses.append(f"\"{col_name}\" = ?")
            values.append(value)
    
    values.append(internal_db_id) # The internal DB ID for the WHERE clause

    update_sql = f"UPDATE {TABLE_NAME} SET {', '.join(set_clauses)} WHERE id = ?" # UPDATED: Use 'id' as key
    
    try:
        cursor.execute(update_sql, values)
        conn.commit()
        # print(f"Trade with DB ID {internal_db_id} updated in DB.")
    except sqlite3.Error as e:
        print(f"Error updating trade with DB ID {internal_db_id} in DB: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_trade_from_db(internal_db_id):
    """Deletes a trade from the database by its internal 'id'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    delete_sql = f"DELETE FROM {TABLE_NAME} WHERE id = ?" # UPDATED: Use 'id' as key
    try:
        cursor.execute(delete_sql, (internal_db_id,))
        conn.commit()
        # print(f"Trade with DB ID {internal_db_id} deleted from DB.")
    except sqlite3.Error as e:
        print(f"Error deleting trade with DB ID {internal_db_id} from DB: {e}")
        conn.rollback()
    finally:
        conn.close()


# Get database name and table name for external use
def get_database_info():
    """Returns the currently configured database name and table name."""
    current_db_name = _get_current_db_name() # Get the name dynamically
    return current_db_name, TABLE_NAME

# Initialize the database when this module is imported
initialize_db()