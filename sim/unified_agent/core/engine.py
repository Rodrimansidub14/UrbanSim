"""
Motor central de simulación que integra CityModel con StreamServer
Se ejecuta en un hilo en segundo plano con un bucle de eventos asincrónico
"""
import asyncio
import threading
import csv
import os
from datetime import datetime
from urban_evolution.model import CityModel
from urban_evolution.streaming import StreamServer
from PyQt5.QtCore import QObject, pyqtSignal


class SimulationEngine(QObject):
    """
    Motor de simulación unificado que ejecuta CityModel y StreamServer
    en un hilo de fondo con un bucle de eventos asincrónico
    """
    
    # Señales de Qt para comunicación entre hilos
    step_completed = pyqtSignal(int)  # Emite el número de paso
    state_updated = pyqtSignal(dict)  # Emite el estado completo
    
    def __init__(self, host="localhost", port=8765, init_settings=None):
        """
        Inicializar el motor de simulación
        
        Args:
            host: Host del WebSocket
            port: Puerto del WebSocket
            init_settings: Diccionario con 'grid_size', 'n_households', 'seed', 'max_steps'
        """
        super().__init__()
        
        # Crear el modelo con las configuraciones iniciales
        if init_settings:
            self.model = CityModel(
                grid_size=init_settings.get('grid_size'),
                n_households=init_settings.get('n_households'),
                seed=init_settings.get('seed')
            )
            print(f"Modelo inicializado con grid={init_settings.get('grid_size')}x{init_settings.get('grid_size')}, hogares={init_settings.get('n_households')}")
        else:
            self.model = CityModel()
            print("Modelo inicializado con configuraciones por defecto")
            
        self.server = StreamServer(self.model, host=host, port=port)
        self.running = False
        self.paused = True  # Comienza en pausa
        self.thread = None
        self.loop = None
        self.step_delay = 0.1  # segundos entre pasos
        
    async def run_async(self):
        """Bucle asincrónico de simulación"""
        # Iniciar el servidor WebSocket
        await self.server.start()
        
        # Enviar estado inicial
        try:
            state = self.server._build_state_message()
            self.state_updated.emit(state)
        except Exception as e:
            print(f"Error construyendo el estado inicial: {e}")
        
        while self.running:
            if not self.paused:
                try:
                    # Avanzar un paso en la simulación
                    self.model.step_once()
                    
                    # Enviar actualización a los clientes WebSocket
                    await self.server.broadcast_tick()
                    
                    # Emitir señales Qt para actualizar la interfaz
                    self.step_completed.emit(self.model.step)
                    state = self.server._build_state_message()
                    self.state_updated.emit(state)
                except Exception as e:
                    print(f"Error en el paso de simulación: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Pequeña pausa para controlar la velocidad de simulación
            await asyncio.sleep(self.step_delay)
            
        # Finalizar cuando se detiene
        await self.server.stop()
        
    def _run_in_thread(self):
        """Método que crea y ejecuta el bucle de eventos asincrónico en un hilo"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.run_async())
        
    def start(self):
        """Iniciar el motor de simulación en un hilo en segundo plano"""
        if self.running:
            return
            
        self.running = True
        self.paused = False
        self.thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self.thread.start()
        print("Motor de simulación iniciado")
        
    def stop(self):
        """Detener el motor de simulación"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        
        # Guardar resultados al detenerse
        run_dir = self.save_results()
        if run_dir:
            self.export_all_visualizations(run_dir)
        print("Motor de simulación detenido")
        
    def pause(self):
        """Pausar la simulación"""
        self.paused = True
        print("Simulación en pausa")
        
    def resume(self):
        """Reanudar la simulación"""
        self.paused = False
        print("Simulación reanudada")
        
    def set_speed(self, delay: float):
        """Establecer la velocidad de simulación (retraso entre pasos en segundos)"""
        self.step_delay = max(0.001, delay)
        
    def send_command(self, command: dict):
        """Enviar un comando a la simulación (seguro para hilos)"""
        if self.loop and self.running:
            asyncio.run_coroutine_threadsafe(
                self._process_command(command),
                self.loop
            )
            
    async def _process_command(self, command: dict):
        """Procesar un comando dentro del bucle asincrónico"""
        import json
        await self.server.process_command(
            json.dumps(command),
            None
        )
    
    def save_results(self):
        """Guardar los resultados de la simulación en un archivo CSV"""
        try:
            # Crear directorio de salida si no existe
            outputs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'run_sim')
            os.makedirs(outputs_dir, exist_ok=True)
            
            # Crear subdirectorio con marca de tiempo
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            run_dir = os.path.join(outputs_dir, f"unified-run-{timestamp}")
            os.makedirs(run_dir, exist_ok=True)
            
            # Ruta del archivo de salida
            output_file = os.path.join(run_dir, 'results.csv')
            
            # Verificar si el modelo tiene registros
            if not self.model.records:
                print("No hay datos de simulación para guardar")
                return run_dir
            
            # Escribir registros en CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = list(self.model.records[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.model.records)
            
            print(f"Resultados guardados en: {output_file}")
            print(f"Total de pasos registrados: {len(self.model.records)}")
            
            return run_dir
            
        except Exception as e:
            print(f"Error al guardar resultados: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def export_all_visualizations(self, run_dir=None):
        """Exportar todas las gráficas y visualizaciones a archivos"""
        try:
            if run_dir is None:
                outputs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'run_sim')
                os.makedirs(outputs_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                run_dir = os.path.join(outputs_dir, f"unified-run-{timestamp}")
                os.makedirs(run_dir, exist_ok=True)
            
            import matplotlib.pyplot as plt
            from urban_evolution.analysis import plot_time_series, save_spatial_maps
            
            if not self.model.records:
                print("No hay datos para exportar")
                return run_dir
            
            import pandas as pd
            df = pd.DataFrame(self.model.records)
            
            # Save time series plots
            plot_time_series(
                df, 
                show=False, 
                savepath=os.path.join(run_dir, "time_series.png")
            )
            print(f"📈 Time series plots saved")
            
            # Guardar mapas espaciales del estado actual
            save_spatial_maps(self.model, run_dir, self.model.step)
            print("Mapas espaciales guardados")
            
            # Exportar el grafo de red si está disponible
            self.export_network_graph(run_dir)
            
            print(f"Todas las visualizaciones exportadas en: {run_dir}")
            return run_dir
            
        except Exception as e:
            print(f"Error al exportar visualizaciones: {e}")
            import traceback
            traceback.print_exc()
            return run_dir
    
    def export_network_graph(self, run_dir):
        """Exportar visualización del grafo de red"""
        try:
            import matplotlib.pyplot as plt
            import networkx as nx
            
            if not hasattr(self.model, 'city_graph') or self.model.city_graph is None:
                print("No hay grafo de red disponible para exportar")
                return
            
            G = self.model.city_graph
            
            fig, ax = plt.subplots(figsize=(12, 12))
            
            pos = {}
            for node in G.nodes():
                i, j = node
                pos[node] = (i, j)
            
            nx.draw_networkx_edges(G, pos, alpha=0.3, ax=ax)
            
            node_colors = []
            for node in G.nodes():
                if 'population' in G.nodes[node]:
                    node_colors.append(G.nodes[node]['population'])
                else:
                    node_colors.append(1)
            
            nx.draw_networkx_nodes(
                G, pos, 
                node_color=node_colors,
                node_size=100,
                cmap=plt.cm.viridis,
                ax=ax
            )
            
            ax.set_title(f"Grafo de la Ciudad - Paso {self.model.step}")
            ax.set_xlabel("Coordenada X")
            ax.set_ylabel("Coordenada Y")
            ax.set_aspect('equal')
            
            network_file = os.path.join(run_dir, f"network_graph_step{self.model.step}.png")
            plt.tight_layout()
            plt.savefig(network_file, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            print(f"Grafo de red guardado en: {network_file}")
            
        except Exception as e:
            print(f"No se pudo exportar el grafo de red: {e}")
