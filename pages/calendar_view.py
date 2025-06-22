import dash
from dash import html, dcc
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import calendar
from datetime import datetime, timedelta

dash.register_page(__name__, path="/calendar", name="Calendar View")

# Load trade data
def load_data():
    conn = sqlite3.connect("sandbox_trades.db")
    df = pd.read_sql_query("SELECT * FROM trades_journal", conn)
    conn.close()
    return df

df = load_data()
df['Entry Time'] = pd.to_datetime(df['Entry Time']).dt.date
df['Realized P&L'] = pd.to_numeric(df['Realized P&L'], errors='coerce').fillna(0)

# Generate full date range for calendar
start_date = df['Entry Time'].min().replace(day=1)
end_date = df['Entry Time'].max().replace(day=1) + pd.offsets.MonthEnd(0)
all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
calendar_df = pd.DataFrame({'date': all_dates})
calendar_df['dow'] = calendar_df['date'].dt.weekday  # 0 = Monday
calendar_df['week'] = calendar_df['date'].apply(lambda x: (x.day - 1) // 7)


# Group by date and sum P&L
pnl_by_date = df.groupby('Entry Time')['Realized P&L'].sum().reset_index(name='realized_pnl')

# Merge into calendar grid
pnl_by_date['Entry Time'] = pd.to_datetime(pnl_by_date['Entry Time'])  # Ensure datetime type
merged = calendar_df.merge(pnl_by_date, left_on='date', right_on='Entry Time', how='left').fillna(0)


# Pivot to grid format
z = merged.pivot(index='dow', columns='week', values='realized_pnl')
z = z.reindex(index=[0, 1, 2, 3, 4, 5, 6])  # Monday to Sunday

# Create heatmap figure
fig = go.Figure(data=go.Heatmap(
    z=z.values,
    x=z.columns.astype(str),
    y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    colorscale='RdYlGn',
    colorbar_title='P&L',
    zmid=0,  # center the scale at 0
    hovertemplate="P&L: %{z}<extra></extra>"
))

fig.update_layout(
    title='📅 Daily Realized P&L Calendar',
    xaxis=dict(showgrid=False, title='Week'),
    yaxis=dict(showgrid=False, title='Day of Week'),
    margin=dict(t=50, l=50, r=50, b=50),
    height=320
)

layout = html.Div([
    html.H2("📅 Trade Calendar View", className="page-title", style={"textAlign": "center"}),
    dcc.Graph(figure=fig, config={"displayModeBar": False})
])
