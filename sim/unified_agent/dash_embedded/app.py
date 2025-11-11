"""
Aplicación Dash integrada para el agente unificado
Versión simplificada que se ejecuta en un hilo en segundo plano
"""
from dash import Dash, html, dcc, Input, Output, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import threading
from .ws_client import DashWebSocketClient


# Instancia global de la aplicación Dash
app = None
ws_client = None


def create_dash_app():
    """Crear y configurar la aplicación Dash"""
    global app, ws_client
    
    # Configurar scripts externos para Plotly
    external_scripts = [
        'https://cdn.plot.ly/plotly-2.26.0.min.js'
    ]
    
    app = Dash(__name__, 
        title="Control de Simulación Urbana",
        update_title="Cargando...",
        external_scripts=external_scripts
    )
    
    # Crear cliente WebSocket
    ws_client = DashWebSocketClient(url="ws://localhost:8765")
    ws_client.start()
    
    # Definir diseño
    app.layout = create_layout()
    
    # Registrar callbacks
    register_callbacks(app, ws_client)
    
    return app


def create_layout():
    """Crear el diseño del panel de control"""
    return html.Div([
        # Encabezado
        html.Div([
            html.H3("Panel en Tiempo Real", 
                    style={'textAlign': 'center', 'color': '#2c3e50', 'margin': '10px'}),
        ]),
        
        # Estado de conexión
        html.Div(id='connection-status', children=[
            html.P("Conectando...", 
                   style={'textAlign': 'center', 'fontSize': '14px', 'fontWeight': 'bold'})
        ]),
        
        # Valores actuales de KPI
        html.Div([
            html.H5("Métricas Actuales", style={'marginTop': '10px', 'marginBottom': '15px'}),
            html.Div(id='current-values', children=[
                html.P("Esperando datos...", style={'textAlign': 'center', 'color': '#6c757d'})
            ], style={'padding': '15px', 'backgroundColor': '#f8f9fa', 
                      'borderRadius': '8px', 'fontSize': '14px'}),
        ], style={'padding': '10px'}),
        
        # Parámetros activos (solo visualización)
        html.Div([
            html.H5("Parámetros Activos", style={'marginTop': '15px', 'marginBottom': '10px'}),
            html.Div(id='params-display', children=[
                html.P("Usa el panel PyQt para ajustar parámetros", 
                       style={'textAlign': 'center', 'color': '#6c757d', 'fontStyle': 'italic'})
            ], style={'padding': '15px', 'backgroundColor': '#e9ecef', 
                      'borderRadius': '8px', 'fontSize': '13px'}),
        ], style={'padding': '10px'}),
        
        # Información de la simulación
        html.Div([
            html.H5("Información de la Simulación", style={'marginTop': '15px', 'marginBottom': '10px'}),
            html.Div(id='sim-info', children=[
                html.P("Paso: 0", id='step-display'),
                html.P("Estado: Inicializando", id='status-display'),
            ], style={'padding': '15px', 'backgroundColor': '#fff3cd', 
                      'borderRadius': '8px', 'fontSize': '13px'}),
        ], style={'padding': '10px'}),
        
        # Intervalo de actualización automática
        dcc.Interval(
            id='interval-component',
            interval=500,  # 500 ms
            n_intervals=0
        ),
        
    ], style={'padding': '15px', 'fontFamily': 'Arial, sans-serif', 'fontSize': '13px', 
              'backgroundColor': '#ffffff', 'minHeight': '100vh'})


def register_callbacks(app, ws_client):
    """Registrar todos los callbacks de Dash"""
    
    @app.callback(
        [Output('connection-status', 'children'),
         Output('current-values', 'children'),
         Output('params-display', 'children'),
         Output('sim-info', 'children')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_display(n):
        """Actualizar la interfaz con los datos más recientes"""
        # Estado de conexión
        if ws_client.connected:
            status = html.P("Conectado a la simulación",
                            style={'textAlign': 'center', 'fontSize': '14px', 
                                   'fontWeight': 'bold', 'color': 'green'})
        else:
            status = html.P("Desconectado",
                            style={'textAlign': 'center', 'fontSize': '14px', 
                                   'fontWeight': 'bold', 'color': 'red'})
        
        # Obtener los KPI más recientes
        kpis = ws_client.get_latest_kpis()
        
        if not kpis:
            current_vals = [html.P("Esperando datos...", 
                                   style={'textAlign': 'center', 'color': '#6c757d'})]
            params_display = [html.P("Sin datos aún")]
            sim_info = [html.P("Inicializando...")]
            return status, current_vals, params_display, sim_info
        
        # Métricas actuales
        current_vals = html.Div([
            html.Div([
                html.Div("Renta Promedio", style={'fontSize': '12px', 'color': '#6c757d'}),
                html.Div(f"${kpis.get('avg_rent', 0):.2f}/mes", 
                         style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#007bff'})
            ], style={'marginBottom': '10px'}),
            
            html.Div([
                html.Div("Tiempo de Viaje", style={'fontSize': '12px', 'color': '#6c757d'}),
                html.Div(f"{kpis.get('avg_travel', 0):.2f} min", 
                         style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#28a745'})
            ], style={'marginBottom': '10px'}),
            
            html.Div([
                html.Div("Tasa de Vacancia", style={'fontSize': '12px', 'color': '#6c757d'}),
                html.Div(f"{kpis.get('vacancy_rate', 0):.1%}", 
                         style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#ffc107'})
            ], style={'marginBottom': '10px'}),
            
            html.Div([
                html.Div("Proporción de Bajos Ingresos", style={'fontSize': '12px', 'color': '#6c757d'}),
                html.Div(f"{kpis.get('share_low_income', 0):.1%}", 
                         style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#17a2b8'})
            ], style={'marginBottom': '10px'}),
            
            html.Div([
                html.Div("Desplazamientos", style={'fontSize': '12px', 'color': '#6c757d'}),
                html.Div(f"{int(kpis.get('displacements', 0))} hogares", 
                         style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#dc3545'})
            ], style={'marginBottom': '10px'}),
            
            html.Div([
                html.Div("Índice de Gentrificación", style={'fontSize': '12px', 'color': '#6c757d'}),
                html.Div(f"{kpis.get('gentr_dispersion', 0):.3f}", 
                         style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#6f42c1'})
            ]),
        ])
        
        # Parámetros actuales
        params = kpis.get('params', {})
        params_display = html.Div([
            html.P(f"Límite de Renta: {params.get('rent_cap', 0):.3f}", 
                   style={'marginBottom': '8px'}),
            html.P(f"Proporción Asequible: {params.get('aff_share', 0):.2f}", 
                   style={'marginBottom': '8px'}),
            html.P(f"Descuento de Vales: {params.get('voucher_discount', 0):.2f}", 
                   style={'marginBottom': '0'}),
        ])
        
        # Información de la simulación
        sim_info = html.Div([
            html.P(f"Paso: {kpis.get('step', 0)}", 
                   style={'marginBottom': '8px', 'fontSize': '14px', 'fontWeight': 'bold'}),
            html.P(f"Puntos de datos: {len(ws_client.history)}", 
                   style={'marginBottom': '0', 'fontSize': '12px'}),
        ])
        
        return status, current_vals, params_display, sim_info


def run_dash_server(host="127.0.0.1", port=8050):
    """Ejecutar el servidor Dash"""
    global app
    if app is None:
        app = create_dash_app()
    
    print(f"Iniciando servidor Dash en http://{host}:{port}")
    app.run(
        host=host,
        port=port,
        debug=False
    )


def start_dash_thread(host="127.0.0.1", port=8050):
    """Iniciar el servidor Dash en un hilo en segundo plano"""
    thread = threading.Thread(
        target=run_dash_server,
        args=(host, port),
        daemon=True,
        name="DashServerThread"
    )
    thread.start()
    print("Hilo del servidor Dash iniciado")
    return thread
