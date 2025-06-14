import dash
from dash import html, dcc

# Create the Dash app
app = dash.Dash(__name__, use_pages=False)
app.title = "Trading Dashboard"

# Layout
app.layout = html.Div([
    html.H2("Trading Dashboard", style={'textAlign': 'center'}),

    dcc.Tabs(id='main-tabs', value='tab-home', children=[
        dcc.Tab(label='🏠 Home', value='tab-home', children=[
            html.Div([
                html.H3("Welcome to the Home Page", style={'textAlign': 'center'}),
            ], style={'padding': '20px'})
        ]),

        dcc.Tab(label='📊 Analytics View', value='tab-analytics', children=[
            html.Div([
                dcc.Tabs(id='analytics-subtabs', value='subtab-pnl-chart', children=[
                    dcc.Tab(label='Pnl Chart', value='subtab-pnl-chart', children=[
                        html.Div([
                            html.H4("P&L Chart Goes Here", style={'textAlign': 'center'})
                        ], style={'padding': '20px'})
                    ]),
                    dcc.Tab(label='Performance Analysis', value='subtab-performance', children=[
                        html.Div([
                            html.H4("Performance Metrics Go Here", style={'textAlign': 'center'})
                        ], style={'padding': '20px'})
                    ]),
                    dcc.Tab(label='KPI', value='subtab-kpi', children=[
                        html.Div([
                            html.H4("KPI Cards or Charts Go Here", style={'textAlign': 'center'})
                        ], style={'padding': '20px'})
                    ]),
                ])
            ])
        ]),

        dcc.Tab(label='⚙️ Config Settings', value='tab-config', children=[
            html.Div([
                html.H3("Configuration Settings Page", style={'textAlign': 'center'}),
            ], style={'padding': '20px'})
        ])
    ])

], style={'width': '100%', 'padding': '20px'})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
