import dash
from dash import html, dcc, Input, Output, State, ctx, dash_table
import pandas as pd
import json
from datetime import datetime
import plotly.graph_objects as go

# Load config
with open("config.json") as f:
    config = json.load(f)

futures_types = config["futures_types"]
daily_risk = config["daily_risk"]
profit_target = config["profit_target"]
default_ftype = config.get("default_futures_type", "MES")
default_size = config.get("default_size", 1)

# Helpers
def calculate_risk(ftype, size, stop):
    mf = futures_types.get(ftype, {}).get("mf", 0)
    return round(stop * mf * size, 2)

def calculate_pnl(ftype, size, points):
    mf = futures_types.get(ftype, {}).get("mf", 0)
    return round(points * mf * size, 2)

# Normalize helper
def normalize_value(value, mapping, default=None):
    if not isinstance(value, str):
        return default
    value_clean = value.strip().lower()
    for key, valid_set in mapping.items():
        if value_clean in valid_set:
            return key
    return default if default is not None else value

# Initial trade log
extra_columns = [
    "Trade came to me", "With Value", "Score", "Execution", "Sizing"
]

all_columns = [
    "Trade #", "Futures Type", "Size", "Stop Loss (pts)",
    "Risk ($)", "Status", "Points Realized", "Realized P&L",
    "Entry Time", "Exit Time"
] + extra_columns

def get_initial_df():
    return pd.DataFrame(columns=all_columns)

# Setup Dash app
app = dash.Dash(__name__)
app.title = "Trading Dashboard V3"

app.layout = html.Div([
    html.H2("📊 Trading Dashboard V3"),

    html.Div([
    html.Button("➕ Add Trade", id="add-trade", n_clicks=0),
    html.Button("🔄 Recalculate", id="recalc-btn", n_clicks=0),
    html.Button("✅ Close Selected Trades", id="close-trades-btn", n_clicks=0)
    ], style={"display": "flex", "gap": "10px", "justifyContent": "flex-start", "marginBottom": "10px"}),


    dash_table.DataTable(
        id="trade-table",
        columns=[
            {"name": col, "id": col, "editable": col not in ["Risk ($)", "Realized P&L", "Entry Time", "Exit Time"]}
            for col in get_initial_df().columns
        ],
        data=get_initial_df().to_dict("records"),
        editable=True,
        row_deletable=True,
        row_selectable="multi",
        selected_rows=[],
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "center"},
        # style_data_conditional=[
        #     # Highlight positive P&L
        #     {
        #         'if': {'filter_query': '{Realized P&L} > 0', 'column_id': 'Realized P&L'},
        #         'backgroundColor': '#d4f4dd',
        #         'color': 'black'
        #     },
        #     # Highlight negative P&L
        #     {
        #         'if': {'filter_query': '{Realized P&L} < 0', 'column_id': 'Realized P&L'},
        #         'backgroundColor': '#fcdede',
        #         'color': 'black'
        #     },
        #     # 🔒 Highlight Closed trades - entire row
        #     {
        #         'if': {'filter_query': '{Status} = "Closed"'},
        #         'backgroundColor': '#f4f4f4',
        #         'color': '#888'
        #     }
        # ]
        style_data_conditional=[
            # 🌹 Full row light rose for negative P&L
            {
                'if': {'filter_query': '{Realized P&L} < 0'},
                'backgroundColor': '#fbeaea',
                'color': 'black'
            },
            # 🌿 Full row light green for positive P&L
            {
                'if': {'filter_query': '{Realized P&L} > 0'},
                'backgroundColor': '#e4f8ec',
                'color': 'black'
            },
            # ⚙️ Optional: Light gray for Closed but no P&L yet (e.g. 0 or empty)
            {
                'if': {
                    'filter_query': '{Status} = "Closed" && ({Realized P&L} = "" || {Realized P&L} = 0)'
                },
                'backgroundColor': '#f4f4f4',
                'color': '#888'
            }
        ]

    ),

    html.Div(id="gauges", style={"display": "flex", "gap": "50px", "marginTop": "30px"}),

    dcc.Store(id="trade-data-store")
])

# Callback to add new trade
@app.callback(
    Output("trade-table", "data"),
    Input("add-trade", "n_clicks"),
    State("trade-table", "data"),
    prevent_initial_call=True
)
def add_trade(n_clicks, data):
    trade_num = len(data) + 1
    default_stop = round(daily_risk / (futures_types[default_ftype]["mf"] * default_size), 2)
    new_trade = {
        "Trade #": trade_num,
        "Futures Type": str(default_ftype),
        "Size": default_size,
        "Stop Loss (pts)": default_stop,
        "Risk ($)": calculate_risk(default_ftype, default_size, default_stop),
        "Status": "Active",
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
    return data + [new_trade]

# Callback to recalculate
@app.callback(
    Output("trade-data-store", "data"),
    Input("recalc-btn", "n_clicks"),
    State("trade-table", "data"),
    prevent_initial_call=True
)
def recalculate_trades(n_clicks, rows):
    df = pd.DataFrame(rows)

    # Define normalization maps
    status_map = {"Active": {"active", "🟠 active", "act"}, "Closed": {"closed", "✅ closed", "cls"}}
    bool_map = {"Yes": {"yes", "y"}, "No": {"no", "n"}}
    score_map = {"A+": {"a+", "a plus"}, "B": {"b"}, "C": {"c"}}
    exec_map = {
        "Calm Execution": {"calm", "calm execution"},
        "Emotional": {"emotional"},
        "FOMO": {"fomo"},
        "Second Guessing": {"second guessing", "2nd guessing"}
    }
    sizing_map = {"Pressing": {"pressing"}, "Base": {"base"}}
    futures_type_map = {ftype: {ftype.lower(), ftype} for ftype in futures_types.keys()}

    for i, row in df.iterrows():
        try:
            df.at[i, "Futures Type"] = normalize_value(row["Futures Type"], futures_type_map, default=default_ftype)
            df.at[i, "Status"] = normalize_value(row["Status"], status_map, default="Active")
            df.at[i, "Trade came to me"] = normalize_value(row["Trade came to me"], bool_map)
            df.at[i, "With Value"] = normalize_value(row["With Value"], bool_map)
            df.at[i, "Score"] = normalize_value(row["Score"], score_map)
            df.at[i, "Execution"] = normalize_value(row["Execution"], exec_map)
            df.at[i, "Sizing"] = normalize_value(row["Sizing"], sizing_map)

            if df.at[i, "Status"] == "Active":
                df.at[i, "Risk ($)"] = calculate_risk(df.at[i, "Futures Type"], int(row["Size"]), float(row["Stop Loss (pts)"]))

            if df.at[i, "Status"] == "Closed":
                if pd.isna(row["Realized P&L"]) or row["Realized P&L"] == "":
                    df.at[i, "Realized P&L"] = calculate_pnl(df.at[i, "Futures Type"], int(row["Size"]), float(row["Points Realized"]))
                    df.at[i, "Exit Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # New logic: calculate Realized P&L if Points Realized is entered but Status not closed yet
            if row.get("Points Realized") not in ["", None]:
                try:
                    df.at[i, "Realized P&L"] = calculate_pnl(
                        df.at[i, "Futures Type"],
                        int(row["Size"]),
                        float(row["Points Realized"])
                    )
                except:
                    df.at[i, "Realized P&L"] = ""


        except Exception as e:
            print(f"Row {i} error: {e}")
    return df.to_dict("records")

#Callback to close selected trades
@app.callback(
    Output("trade-table", "data", allow_duplicate=True),
    Input("close-trades-btn", "n_clicks"),
    State("trade-table", "data"),
    State("trade-table", "selected_rows"),
    prevent_initial_call=True
)
def close_selected_trades(n_clicks, data, selected_rows):
    if not selected_rows:
        return data  # Nothing selected

    for i in selected_rows:
        row = data[i]
        # Only close if not already closed
        if str(row.get("Status", "")).lower() != "closed":
            data[i]["Status"] = "Closed"
            data[i]["Exit Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                points = float(row.get("Points Realized", 0))
                size = int(row.get("Size", 1))
                ftype = row.get("Futures Type", default_ftype)
                data[i]["Realized P&L"] = calculate_pnl(ftype, size, points)
            except:
                data[i]["Realized P&L"] = ""
    return data


# Callback to update table and gauges
@app.callback(
    Output("trade-table", "data", allow_duplicate=True),
    Output("gauges", "children"),
    Input("trade-data-store", "data"),
    Input("trade-table", "data"),
    prevent_initial_call=True
)
def update_dashboard(store_data, table_data):
    df = pd.DataFrame(store_data if store_data else table_data)
    # Ensure numeric values and handle missing data
    df["Risk ($)"] = pd.to_numeric(df["Risk ($)"], errors="coerce").fillna(0)
    df["Realized P&L"] = pd.to_numeric(df["Realized P&L"], errors="coerce").fillna(0)

    active_risk = df[df["Status"] == "Active"]["Risk ($)"].sum()
    realized_pnl = df[df["Status"] == "Closed"]["Realized P&L"].sum()

    available_risk = max(0, daily_risk + realized_pnl - active_risk)


    gauge_risk = go.Figure(go.Indicator(
        mode="gauge+number",
        value=available_risk,
        title={"text": "Available Risk ($)"},
        gauge={"axis": {"range": [0, daily_risk + profit_target]}}
    ))

    gauge_pnl = go.Figure(go.Indicator(
        mode="gauge+number",
        value=realized_pnl,
        title={"text": "Realized P&L ($)"},
        gauge={"axis": {"range": [-daily_risk, profit_target]}}
    ))

    return df.to_dict("records"), [
        dcc.Graph(figure=gauge_risk, style={"width": "45%"}),
        dcc.Graph(figure=gauge_pnl, style={"width": "45%"})
    ]

if __name__ == '__main__':
    app.run(debug=True)
