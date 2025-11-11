"""
Embedded Dash application for the unified agent
Simplified version that runs in a background thread
"""
from dash import Dash, html, dcc, Input, Output, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import threading
from .ws_client import DashWebSocketClient


# Global Dash app instance
app = None
ws_client = None


def create_dash_app():
    """Create and configure the Dash application"""
    global app, ws_client
    
    # Configure external scripts for Plotly
    external_scripts = [
        'https://cdn.plot.ly/plotly-2.26.0.min.js'
    ]
    
    app = Dash(__name__, 
               title="Urban Simulation Control",
               update_title="Loading...",
               external_scripts=external_scripts)
    
    # Create WebSocket client
    ws_client = DashWebSocketClient(url="ws://localhost:8765")
    ws_client.start()
    
    # Set layout
    app.layout = create_layout()
    
    # Register callbacks
    register_callbacks(app, ws_client)
    
    return app


def create_layout():
    """Create the dashboard layout"""
    return html.Div([
        # Header
        html.Div([
            html.H3("📊 Real-Time Dashboard", 
                   style={'textAlign': 'center', 'color': '#2c3e50', 'margin': '10px'}),
        ]),
        
        # Connection status
        html.Div(id='connection-status', children=[
            html.P("🔴 Connecting...", 
                  style={'textAlign': 'center', 'fontSize': '14px', 'fontWeight': 'bold'})
        ]),
        
        # Current KPI values - Expanded view
        html.Div([
            html.H5("📈 Current Metrics", style={'marginTop': '10px', 'marginBottom': '15px'}),
            html.Div(id='current-values', children=[
                html.P("Waiting for data...", style={'textAlign': 'center', 'color': '#6c757d'})
            ], style={'padding': '15px', 'backgroundColor': '#f8f9fa', 
                     'borderRadius': '8px', 'fontSize': '14px'}),
        ], style={'padding': '10px'}),
        
        # Parameters status (read-only display)
        html.Div([
            html.H5("⚙️ Active Parameters", style={'marginTop': '15px', 'marginBottom': '10px'}),
            html.Div(id='params-display', children=[
                html.P("Use PyQt panel to adjust parameters", 
                      style={'textAlign': 'center', 'color': '#6c757d', 'fontStyle': 'italic'})
            ], style={'padding': '15px', 'backgroundColor': '#e9ecef', 
                     'borderRadius': '8px', 'fontSize': '13px'}),
        ], style={'padding': '10px'}),
        
        # Simulation info
        html.Div([
            html.H5("🎮 Simulation Info", style={'marginTop': '15px', 'marginBottom': '10px'}),
            html.Div(id='sim-info', children=[
                html.P("Step: 0", id='step-display'),
                html.P("Status: Initializing", id='status-display'),
            ], style={'padding': '15px', 'backgroundColor': '#fff3cd', 
                     'borderRadius': '8px', 'fontSize': '13px'}),
        ], style={'padding': '10px'}),
        
        # Auto-refresh interval
        dcc.Interval(
            id='interval-component',
            interval=500,  # 500ms
            n_intervals=0
        ),
        
    ], style={'padding': '15px', 'fontFamily': 'Arial, sans-serif', 'fontSize': '13px', 
             'backgroundColor': '#ffffff', 'minHeight': '100vh'})


def register_callbacks(app, ws_client):
    """Register all Dash callbacks"""
    
    @app.callback(
        [Output('connection-status', 'children'),
         Output('current-values', 'children'),
         Output('params-display', 'children'),
         Output('sim-info', 'children')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_display(n):
        """Update display with latest data"""
        # Connection status
        if ws_client.connected:
            status = html.P("🟢 Connected to Simulation",
                          style={'textAlign': 'center', 'fontSize': '14px', 
                                'fontWeight': 'bold', 'color': 'green'})
        else:
            status = html.P("🔴 Disconnected",
                          style={'textAlign': 'center', 'fontSize': '14px', 
                                'fontWeight': 'bold', 'color': 'red'})
        
        # Get latest KPIs
        kpis = ws_client.get_latest_kpis()
        
        if not kpis:
            current_vals = [html.P("Waiting for data...", 
                                  style={'textAlign': 'center', 'color': '#6c757d'})]
            params_display = [html.P("No data yet")]
            sim_info = [html.P("Initializing...")]
            return status, current_vals, params_display, sim_info
        
        # Current KPI values - styled cards
        current_vals = html.Div([
            html.Div([
                html.Div("💰 Average Rent", style={'fontSize': '12px', 'color': '#6c757d'}),
                html.Div(f"${kpis.get('avg_rent', 0):.2f}/month", 
                        style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#007bff'})
            ], style={'marginBottom': '10px'}),
            
            html.Div([
                html.Div("🚗 Travel Time", style={'fontSize': '12px', 'color': '#6c757d'}),
                html.Div(f"{kpis.get('avg_travel', 0):.2f} min", 
                        style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#28a745'})
            ], style={'marginBottom': '10px'}),
            
            html.Div([
                html.Div("📦 Vacancy Rate", style={'fontSize': '12px', 'color': '#6c757d'}),
                html.Div(f"{kpis.get('vacancy_rate', 0):.1%}", 
                        style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#ffc107'})
            ], style={'marginBottom': '10px'}),
            
            html.Div([
                html.Div("👥 Low Income Share", style={'fontSize': '12px', 'color': '#6c757d'}),
                html.Div(f"{kpis.get('share_low_income', 0):.1%}", 
                        style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#17a2b8'})
            ], style={'marginBottom': '10px'}),
            
            html.Div([
                html.Div("🏘️ Displacements", style={'fontSize': '12px', 'color': '#6c757d'}),
                html.Div(f"{int(kpis.get('displacements', 0))} households", 
                        style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#dc3545'})
            ], style={'marginBottom': '10px'}),
            
            html.Div([
                html.Div("📊 Gentrification Index", style={'fontSize': '12px', 'color': '#6c757d'}),
                html.Div(f"{kpis.get('gentr_dispersion', 0):.3f}", 
                        style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#6f42c1'})
            ]),
        ])
        
        # Parameters display
        params = kpis.get('params', {})
        params_display = html.Div([
            html.P(f"🔒 Rent Cap: {params.get('rent_cap', 0):.3f}", 
                  style={'marginBottom': '8px'}),
            html.P(f"🏘️ Affordable Share: {params.get('aff_share', 0):.2f}", 
                  style={'marginBottom': '8px'}),
            html.P(f"🎫 Voucher Discount: {params.get('voucher_discount', 0):.2f}", 
                  style={'marginBottom': '0'}),
        ])
        
        # Simulation info
        sim_info = html.Div([
            html.P(f"⏱️ Step: {kpis.get('step', 0)}", 
                  style={'marginBottom': '8px', 'fontSize': '14px', 'fontWeight': 'bold'}),
            html.P(f"📈 Data points: {len(ws_client.history)}", 
                  style={'marginBottom': '0', 'fontSize': '12px'}),
        ])
        
        return status, current_vals, params_display, sim_info


def run_dash_server(host="127.0.0.1", port=8050):
    """Run the Dash server"""
    global app
    if app is None:
        app = create_dash_app()
    
    print(f"🌐 Starting Dash server on http://{host}:{port}")
    app.run(
        host=host,
        port=port,
        debug=False
    )


def start_dash_thread(host="127.0.0.1", port=8050):
    """Start Dash server in a background thread"""
    thread = threading.Thread(
        target=run_dash_server,
        args=(host, port),
        daemon=True,
        name="DashServerThread"
    )
    thread.start()
    print("✅ Dash server thread started")
    return thread
