import dash
from dash import dcc, html

# Initialize the Dash app
# use_pages=True enables the multi-page feature
# pages_folder='pages' tells Dash where to find your page files (like daily_helper.py)
app = dash.Dash(__name__, use_pages=True, pages_folder='pages')

# Suppress callback exceptions for multi-page apps.
# This prevents errors from callbacks for pages not currently in the layout.
app.config.suppress_callback_exceptions = True

# Define the main layout of the application
# This includes the sidebar and the area where page content will be displayed
app.layout = html.Div([
    #html.H1("Trading Dashboard", style={'textAlign': 'center', 'marginBottom': '20px'}),

    # dcc.Location component is crucial for multi-page apps
    # It reads the current URL and allows callbacks (implicitly handled by dash.page_registry)
    # to react to URL changes and load the correct page.
    dcc.Location(id='url', refresh=False),

    # Main content area: Sidebar + Page Content
    html.Div([
        # Sidebar
        html.Div([
            html.H2("Navigation", style={'textAlign': 'center', 'color': 'white'}),
            html.Hr(style={'borderColor': 'white'}),
            html.Div(
                children=[
                    html.P(dcc.Link(f"{page['name']}", href=page["path"], style={'color': 'white', 'textDecoration': 'none', 'padding': '10px 0', 'display': 'block'}))
                    for page in dash.page_registry.values()
                    if page["name"] in ["Daily Helper"] # Only list pages you've created so far
                    # We will add "Historical Data" and "Analytical Views" links here as we build them.
                    # You can also add a dedicated "Home" page link here later if you create a pages/home.py
                ],
                style={'padding': '10px'}
            ),
        ], style={
            'width': '200px',
            'minHeight': '100vh', # Full height sidebar
            'backgroundColor': '#333', # Dark background
            'padding': '20px',
            'boxShadow': '2px 0 5px rgba(0,0,0,0.1)',
            'position': 'fixed', # Fixed sidebar
            'left': 0, 'top': 0, 'zIndex': 1000 # Ensure it stays on top
        }),

        # Page Content Area
        html.Div([
            dash.page_container # This is where the content of each registered page will be displayed
        ], style={
            'marginLeft': '220px', # Space for sidebar (200px width + 20px padding)
            'padding': '20px',
            'flexGrow': 1 # Allow content area to grow
        })
    ], style={'display': 'flex'}), # Flex container for sidebar and page content

    # Global components that are shared across all pages or manage global state/actions
    # These should NOT be inside any specific page's layout, but in the main app layout
    html.Div(id='debug-output', style={'marginTop': '20px', 'color': 'red'}), # For debugging messages
    dcc.Store(id='current-pressing-index', data=0), # Global state for pressing roadmap
    dcc.Download(id="download-dataframe-xlsx"),     # For triggering file downloads
    dcc.Download(id="download-saved-trades"),      # For triggering saved data download
])

# Run the Dash app
if __name__ == '__main__':
    app.run(debug=True)