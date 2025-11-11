"""
Cliente WebSocket simplificado para Dash embebido
Reutiliza el cliente de dash_app pero de forma simplificada
"""
import asyncio
import json
import websockets
from collections import deque
import threading


class DashWebSocketClient:
    """Cliente WebSocket para Dash embebido en Qt"""
    
    def __init__(self, url="ws://localhost:8765", max_history=300):
        self.url = url
        self.max_history = max_history
        self.history = deque(maxlen=max_history)
        self.latest_state = None
        self.connected = False
        self.running = False
        self.thread = None
        self.loop = None
        self.websocket = None
        
    def start(self):
        """Iniciar el cliente en un hilo en segundo plano"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
    def _run_loop(self):
        """Ejecutar el bucle de eventos asincrónico"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect_and_listen())
        
    async def _connect_and_listen(self):
        """Conectarse y escuchar mensajes"""
        while self.running:
            try:
                async with websockets.connect(self.url) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    
                    async for message in websocket:
                        data = json.loads(message)
                        self._process_data(data)
                        
            except Exception as e:
                self.connected = False
                print(f"Error en conexión WebSocket de Dash: {e}")
                await asyncio.sleep(2)
                
    def _process_data(self, data):
        """Procesar los datos recibidos"""
        if data.get('type') == 'state_update':
            self.latest_state = data
            kpis = data.get('kpis', {})
            kpis['step'] = data.get('step', 0)
            self.history.append(kpis)
            
    def send_command(self, command: dict):
        """Enviar un comando"""
        if self.websocket and self.loop:
            asyncio.run_coroutine_threadsafe(
                self._send(command),
                self.loop
            )
            
    async def _send(self, command: dict):
        """Método auxiliar para enviar"""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(command))
            except Exception as e:
                print(f"Error al enviar comando: {e}")
                
    def get_history_df(self):
        """Obtener el historial como un DataFrame"""
        import pandas as pd
        if not self.history:
            return pd.DataFrame()
        return pd.DataFrame(list(self.history))
        
    def get_latest_kpis(self):
        """Obtener los últimos indicadores (KPIs)"""
        if self.latest_state:
            return self.latest_state.get('kpis', {})
        return {}
        
    def stop(self):
        """Detener el cliente"""
        self.running = False
