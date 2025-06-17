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

def initialize_db():
    """Creates the trades_journal table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    column_definitions = []
    for col in COLUMNS_TO_STORE:
        if col in ["Trade #", "Size", "Stop Loss (pts)", "Risk ($)", "Points Realized", "Realized P&L"]:
            column_definitions.append(f"\"{col}\" REAL") # Use REAL for numbers (floats/integers)
        else:
            column_definitions.append(f"\"{col}\" TEXT") # Use TEXT for strings/dropdowns

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {', '.join(column_definitions)}
    );
    """
    cursor.execute(create_table_sql)
    conn.commit()
    conn.close()
    print(f"Database '{DATABASE_NAME}' and table '{TABLE_NAME}' initialized (if not already existing).")

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

# Initialize the database when this module is imported
initialize_db()