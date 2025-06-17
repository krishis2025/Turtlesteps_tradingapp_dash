import dash
from dash import Dash, dash_table, html
import pandas as pd

app = Dash(__name__)

# Sample Data
df = pd.DataFrame({
    "Trade #": [1, 2, 3],
    "Futures Type": ["MES", "ES", "MES"],
    "Size": [1, 2, 3],
    "Status": ["Active", "Closed", "Closed"],
    "Realized P&L": [0.0, 125.0, -50.0]
})

app.layout = html.Div([
    html.H2("Streamlit-like Table in Dash"),
    dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict("records"),
        style_table={"overflowX": "auto", "width": "100%"},
        style_cell={
            "textAlign": "center",
            "padding": "8px",
            "fontFamily": "sans-serif",
            "fontSize": "14px",
        },
        style_header={
            "backgroundColor": "#f2f2f2",
            "fontWeight": "bold",
            "border": "none"
        },
        style_data={
            "border": "none"
        },
        style_data_conditional=[
            {
                "if": {"state": "active"},
                "backgroundColor": "#f9f9f9",
                "border": "none"
            },
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#f7f7f7"
            },
            {
                "if": {
                    "filter_query": "{Realized P&L} > 0",
                    "column_id": "Realized P&L"
                },
                "color": "green"
            },
            {
                "if": {
                    "filter_query": "{Realized P&L} < 0",
                    "column_id": "Realized P&L"
                },
                "color": "red"
            }
        ]
    )
], style={"padding": "20px"})

if __name__ == '__main__':
    app.run(debug=True)
