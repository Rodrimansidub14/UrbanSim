"""Network visualization panel with spatial graph and community detection."""
import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QColor
import networkx as nx


class NetworkPanel(QWidget):
    """Urban network visualization with nodes as neighborhoods and edges as roads."""
    
    def __init__(self):
        super().__init__()
        self.G = None
        self.graph_built = False
        self.current_grid_size = None
        self.pos = None
        self.adj = None
        self.node_id_map = {}
        self.last_state = None
        self.show_communities = False
        self.color_by = 'population'
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Controls
        controls = self.create_controls()
        layout.addLayout(controls)
        
        # Graph view
        self.graph_widget = pg.GraphicsLayoutWidget()
        self.graph_widget.setBackground('w')
        layout.addWidget(self.graph_widget)
        
        # Create plot
        self.plot = self.graph_widget.addPlot()
        self.plot.setAspectLocked(True)
        self.plot.hideAxis('left')
        self.plot.hideAxis('bottom')
        self.plot.setTitle("Red Urbana", size='12pt')
        
        # Draw edges and nodes manually for better rendering
        self.edge_items = []
        self.node_scatter = pg.ScatterPlotItem(size=15, pen=pg.mkPen(color='w', width=2))
        
        # Legend
        self.legend_label = QLabel("Red no inicializada")
        layout.addWidget(self.legend_label)
        
    def create_controls(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        
        # Color by selector
        layout.addWidget(QLabel("Colorear por:"))
        self.color_selector = QComboBox()
        self.color_selector.addItems(['Población', 'Renta', 'Gentrificación', 'Congestión (v/c)'])
        self.color_selector.currentTextChanged.connect(self.on_color_changed)
        layout.addWidget(self.color_selector)
        
        # Communities checkbox
        self.communities_check = QCheckBox("Mostrar Comunidades")
        self.communities_check.stateChanged.connect(self.on_communities_toggle)
        layout.addWidget(self.communities_check)
        
        layout.addStretch()
        return layout
        
    def on_color_changed(self, text):
        mapping = {
            'Población': 'population',
            'Renta': 'rent',
            'Gentrificación': 'gentrification',
            'Congestión (v/c)': 'congestion'
        }
        self.color_by = mapping.get(text, 'population')
        if self.last_state:
            self.update_network(self.last_state)
            
    def on_communities_toggle(self, state):
        self.show_communities = (state == 2)
        if self.last_state:
            self.update_network(self.last_state)
            
    @pyqtSlot(dict)
    def update_network(self, state: dict):
        self.last_state = state
        if 'network' not in state:
            self.generate_grid_network(state)
        else:
            self.render_network(state['network'])
            
    def build_city_network(self, n_rows: int, n_cols: int):
        """Build spatial network graph once, rebuild if grid size changes."""
        if self.graph_built and self.current_grid_size == (n_rows, n_cols):
            return
        
        self.current_grid_size = (n_rows, n_cols)
        self.G = nx.grid_2d_graph(n_rows, n_cols)
        
        # Crear mapeo de coordenadas a IDs lineales
        node_id = 0
        for i in range(n_rows):
            for j in range(n_cols):
                self.node_id_map[(i, j)] = node_id
                node_id += 1
        
        # Extraer posiciones fijas
        pos_list = []
        for i in range(n_rows):
            for j in range(n_cols):
                pos_list.append([j, n_rows - i - 1])  # y invertida para visualización
        self.pos = np.array(pos_list, dtype=np.float32)
        
        # Construir matriz de adyacencia (FIJA, no cambia)
        n_nodes = n_rows * n_cols
        self.adj = np.zeros((n_nodes, n_nodes), dtype=np.int32)
        
        edge_count = 0
        for (u, v) in self.G.edges():
            u_id = self.node_id_map[u]
            v_id = self.node_id_map[v]
            self.adj[u_id, v_id] = 1
            self.adj[v_id, u_id] = 1
            edge_count += 1
        
        print(f"✅ Red construida: {len(self.G.nodes)} nodos, {edge_count} aristas")
        print(f"📊 Matriz de adyacencia: shape={self.adj.shape}, suma={self.adj.sum()}")
        
        # DEBUG: Verificar algunas conexiones
        edges_in_adj = np.sum(self.adj) // 2  # Dividir por 2 porque es simétrica
        print(f"🔍 Verificación: {edges_in_adj} conexiones en matriz de adyacencia")
        print(f"🔍 Primeras 5 aristas: {list(self.G.edges())[:5]}")
        
        # DEBUG: Verificar que posiciones y adyacencia están bien
        print(f"🔍 Posiciones min: {self.pos.min(axis=0)}, max: {self.pos.max(axis=0)}")
        print(f"🔍 Rango X: [{self.pos[:,0].min()}, {self.pos[:,0].max()}]")
        print(f"🔍 Rango Y: [{self.pos[:,1].min()}, {self.pos[:,1].max()}]")
        
        # NUEVA SOLUCIÓN: Dibujar aristas manualmente
        # Limpiar aristas anteriores
        for item in self.edge_items:
            self.plot.removeItem(item)
        self.edge_items = []
        
        # Dibujar cada arista como una línea individual
        edge_pen = pg.mkPen(color=(100, 100, 100, 200), width=2)
        edges_drawn = 0
        
        for (u, v) in self.G.edges():
            u_id = self.node_id_map[u]
            v_id = self.node_id_map[v]
            
            # Posiciones de inicio y fin
            x_coords = [self.pos[u_id, 0], self.pos[v_id, 0]]
            y_coords = [self.pos[u_id, 1], self.pos[v_id, 1]]
            
            # Crear línea individual
            line = pg.PlotDataItem(x_coords, y_coords, pen=edge_pen)
            self.plot.addItem(line)
            self.edge_items.append(line)
            edges_drawn += 1
        
        print(f"✅ {edges_drawn} aristas dibujadas manualmente")
        
        # Dibujar nodos encima de las aristas
        if hasattr(self, 'node_scatter') and self.node_scatter in self.plot.items:
            self.plot.removeItem(self.node_scatter)
        
        self.node_scatter = pg.ScatterPlotItem(
            pos=self.pos,
            size=15,
            pen=pg.mkPen(color='w', width=2),
            brush=pg.mkBrush(150, 150, 150, 200),
            symbol='o'
        )
        self.plot.addItem(self.node_scatter)
        
        # Ajustar vista para mostrar toda la red
        self.plot.setXRange(-0.5, n_cols - 0.5, padding=0.1)
        self.plot.setYRange(-0.5, n_rows - 0.5, padding=0.1)
        
        self.graph_built = True
        print(f"🎨 Red renderizada: {n_nodes} nodos, {edges_drawn} aristas")
        print(f"🎯 Vista ajustada a X:[-0.5,{n_cols-0.5}], Y:[-0.5,{n_rows-0.5}]")
    
    def generate_grid_network(self, state: dict):
        """Actualizar métricas de red sin recrear estructura"""
        try:
            spatial = state.get('spatial', {})
            
            if 'rent' not in spatial:
                return
            
            # DEBUG: Ver qué datos espaciales están disponibles
            print(f"🔍 Claves en spatial: {list(spatial.keys())}")
            
            rent_grid = np.array(spatial['rent'])
            
            # Obtener población - la clave correcta es 'pop' (no 'population')
            if 'pop' in spatial:
                pop_grid = np.array(spatial['pop'])
                print(f"✅ Población encontrada: suma={pop_grid.sum()}, promedio={pop_grid.mean():.1f}")
            else:
                pop_grid = rent_grid * 0
                print(f"❌ No se encontró 'pop' en spatial, usando ceros")
                print(f"   Claves disponibles: {list(spatial.keys())}")
            
            n_rows, n_cols = rent_grid.shape
            
            # CONSTRUIR grafo (primera vez O si cambió el tamaño)
            # build_city_network se encarga de verificar si necesita reconstruir
            self.build_city_network(n_rows, n_cols)
            
            # ACTUALIZAR métricas (no recrear estructura)
            self.update_network_metrics(state, n_rows, n_cols, rent_grid, pop_grid)
            
        except Exception as e:
            print(f"⚠️  Error generando red en grid: {e}")
            import traceback
            traceback.print_exc()
    
    def update_network_metrics(self, state: dict, n_rows: int, n_cols: int, rent_grid, pop_grid):
        """Actualizar métricas de nodos y aristas SIN recrear el grafo"""
        # Verificar que el grafo esté construido y sea del tamaño correcto
        if not self.graph_built or self.current_grid_size != (n_rows, n_cols):
            print(f"⚠️  Grafo no construido o tamaño incorrecto, esperando construcción...")
            return
        
        # Calcular población por nodo desde el grid de población
        pop_by_node = pop_grid.flatten()
        
        # Calcular p_high (fracción de altos ingresos) por nodo
        # Usar 'gentr' del modelo (gentrification index = pop_high / pop_total)
        spatial = state.get('spatial', {})
        if 'gentr' in spatial:
            gentr_grid = np.array(spatial['gentr'])
            p_high_by_node = gentr_grid.flatten()
        else:
            # Fallback: asumir distribución uniforme
            p_high_by_node = np.full(n_rows * n_cols, 0.3)
        
        # ACTUALIZAR atributos de nodos (NO recrear nodos)
        nodes_list = []
        node_id = 0
        for i in range(n_rows):
            for j in range(n_cols):
                node_data = {
                    'id': node_id,
                    'x': j,
                    'y': n_rows - i - 1,
                    'rent': float(rent_grid[i, j]),
                    'pop': float(pop_by_node[node_id]),
                    'p_high': float(p_high_by_node[node_id])
                }
                # Actualizar atributos en el grafo NetworkX
                if (i, j) in self.G.nodes:
                    self.G.nodes[(i, j)].update(node_data)
                nodes_list.append(node_data)
                node_id += 1
        
        # ACTUALIZAR atributos de aristas (flujo, capacidad, v/c)
        edges_list = []
        step = state.get('kpis', {}).get('step', 0)
        for u, v in self.G.edges():
            # Generar flujo simulado (varía por step para ver cambios)
            flow = 100 + int(50 * np.sin(step * 0.1 + u[0] + v[0]))
            cap = 300
            tt0 = 10.0
            
            # BPR travel time
            vc = flow / cap if cap > 0 else 0
            tt = self.bpr_travel_time(tt0, flow, cap)
            
            u_id = self.node_id_map[u]
            v_id = self.node_id_map[v]
            
            edge_data = {
                'u': u_id,
                'v': v_id,
                'flow': flow,
                'cap': cap,
                'vc': vc,
                'tt': tt
            }
            # Actualizar atributos en el grafo NetworkX
            self.G.edges[(u, v)].update(edge_data)
            edges_list.append(edge_data)
        
        # Calcular métricas de NetworkX
        self.compute_network_metrics()
        
        # Preparar datos para visualización
        network_data = {
            'nodes': nodes_list,
            'edges': edges_list,
            'stats': {
                'avg_pop': float(np.mean(pop_by_node)),
                'avg_rent': float(np.mean(rent_grid)),
                'avg_vc': float(np.mean([e['vc'] for e in edges_list]))
            }
        }
        
        # SOLO actualizar colores (NO llamar setData)
        self.update_colors(network_data)
    
    def bpr_travel_time(self, tt0, flow, cap, alpha=0.15, beta=4.0):
        """Calcular tiempo de viaje con función BPR"""
        vc = flow / cap if cap > 0 else 0
        return tt0 * (1.0 + alpha * (vc ** beta))
    
    def compute_network_metrics(self):
        """Calcular métricas de red con NetworkX"""
        if self.G is None or len(self.G.nodes) == 0:
            return
        
        try:
            # Grado promedio
            degrees = dict(self.G.degree())
            for node in self.G.nodes():
                self.G.nodes[node]['degree'] = degrees[node]
            
            # Betweenness centrality (solo si la red no es muy grande)
            if len(self.G.nodes) < 100:
                betweenness = nx.betweenness_centrality(self.G)
                for node in self.G.nodes():
                    self.G.nodes[node]['betweenness'] = betweenness[node]
            
            # Detectar comunidades si está activado
            if self.show_communities and len(self.G.nodes) > 0:
                communities = nx.community.greedy_modularity_communities(self.G)
                community_map = {}
                for idx, comm in enumerate(communities):
                    for node in comm:
                        community_map[node] = idx
                        self.G.nodes[node]['community'] = idx
                        
        except Exception as e:
            print(f"⚠️  Error calculando métricas de red: {e}")
            
    def update_colors(self, network_data: dict):
        """Actualizar SOLO colores de nodos (sin recrear el canvas)"""
        try:
            nodes = network_data['nodes']
            edges = network_data.get('edges', [])
            
            if not nodes:
                return
            
            # Calcular colores normalizados
            node_colors = self.compute_node_colors_normalized(nodes)
            
            # NUEVA SOLUCIÓN: Actualizar solo los colores de los nodos
            # Las aristas ya están dibujadas y no cambian
            if self.pos is not None and hasattr(self, 'node_scatter'):
                # Actualizar colores del scatter plot
                brushes = [pg.mkBrush(*color) for color in node_colors]
                self.node_scatter.setBrush(brushes)
            
            # Actualizar leyenda
            self.update_legend(nodes, edges)
            
        except Exception as e:
            print(f"⚠️  Error actualizando colores: {e}")
            import traceback
            traceback.print_exc()
    
    def render_network(self, network_data: dict):
        """DEPRECADO: Solo se usa si no hay grafo construido"""
        # Este método ya no debería llamarse si build_city_network funciona
        print("⚠️  render_network llamado (debería usar update_colors)")
        self.update_colors(network_data)
            
    def compute_node_colors_normalized(self, nodes: list) -> list:
        """Calcular colores de nodos con normalización min-max robusta"""
        colors = []
        
        # PRIORIDAD: Si "Mostrar Comunidades" está activado, colorear por comunidad
        if self.show_communities and self.G:
            # Generar colores distintos para cada comunidad
            community_colors = [
                (255, 100, 100, 200),  # Rojo
                (100, 255, 100, 200),  # Verde
                (100, 100, 255, 200),  # Azul
                (255, 255, 100, 200),  # Amarillo
                (255, 100, 255, 200),  # Magenta
                (100, 255, 255, 200),  # Cyan
                (255, 150, 100, 200),  # Naranja
                (150, 100, 255, 200),  # Violeta
                (100, 255, 150, 200),  # Verde claro
                (255, 100, 150, 200),  # Rosa
            ]
            
            # Asignar color según comunidad del nodo
            for i, node_key in enumerate(sorted(self.G.nodes())):
                community_id = self.G.nodes[node_key].get('community', 0)
                color_idx = community_id % len(community_colors)
                colors.append(community_colors[color_idx])
            
            return colors
        
        # Si no hay comunidades, colorear según métrica seleccionada
        if self.color_by == 'rent':
            values = np.array([n.get('rent', 0) for n in nodes])
            min_val, max_val = values.min(), values.max()
            
            for val in values:
                # Normalización min-max
                if max_val > min_val:
                    norm = (val - min_val) / (max_val - min_val)
                else:
                    norm = 0.5
                # Azul (bajo) → Rojo (alto)
                r = int(255 * norm)
                b = int(255 * (1 - norm))
                colors.append((r, 0, b, 200))
                
        elif self.color_by == 'population':
            values = np.array([n.get('pop', 0) for n in nodes])
            max_val = values.max()
            
            for val in values:
                norm = val / max_val if max_val > 0 else 0
                # Verde oscuro (bajo) → Verde brillante (alto)
                g = int(100 + 155 * norm)
                colors.append((0, g, 50, 200))
                
        elif self.color_by == 'gentrification':
            # p_high ya está normalizado [0,1]
            values = np.array([n.get('p_high', 0) for n in nodes])
            
            for val in values:
                # Amarillo (bajo) → Naranja → Rojo (alto)
                r = 255
                g = int(255 * (1 - val * 0.8))
                b = int(50 * (1 - val))
                colors.append((r, g, b, 200))
                
        elif self.color_by == 'congestion':
            # Calcular congestión promedio por nodo (desde aristas adyacentes)
            node_congestion = np.zeros(len(nodes))
            
            if self.G:
                for i, node_key in enumerate(sorted(self.G.nodes())):
                    # Promedio de v/c de aristas adyacentes
                    neighbors = list(self.G.neighbors(node_key))
                    if neighbors:
                        vc_vals = [self.G.edges[(node_key, n)].get('vc', 0) for n in neighbors]
                        node_congestion[i] = np.mean(vc_vals)
            
            max_cong = node_congestion.max() if node_congestion.max() > 0 else 1
            
            for cong in node_congestion:
                norm = cong / max_cong
                # Verde (bajo) → Amarillo → Rojo (alto)
                if norm < 0.5:
                    r = int(255 * norm * 2)
                    g = 255
                else:
                    r = 255
                    g = int(255 * (1 - (norm - 0.5) * 2))
                colors.append((r, g, 0, 200))
                
        else:
            for _ in nodes:
                colors.append((100, 100, 100, 200))
                
        return colors
        

    def update_legend(self, nodes: list, edges: list):
        """Actualizar leyenda con estadísticas de red"""
        try:
            n_nodes = len(nodes)
            n_edges = len(edges)
            
            avg_rent = np.mean([n.get('rent', 0) for n in nodes])
            avg_pop = np.mean([n.get('pop', 0) for n in nodes])
            
            # Calcular v/c promedio
            vc_ratios = [e.get('vc', 0) for e in edges]
            avg_vc = np.mean(vc_ratios) if vc_ratios else 0
            
            # Calcular grado promedio 
            avg_degree = 0
            n_communities = 0
            if self.G:
                degrees = [d for n, d in self.G.degree()]
                avg_degree = np.mean(degrees) if degrees else 0
                
                # Contar comunidades si están activas
                if self.show_communities:
                    communities_set = set()
                    for node in self.G.nodes():
                        comm_id = self.G.nodes[node].get('community', 0)
                        communities_set.add(comm_id)
                    n_communities = len(communities_set)
            
            legend_text = (
                f"Nodos: {n_nodes} | Aristas: {n_edges} | "
                f"Renta Prom: ${avg_rent:.0f} | Población: {avg_pop:.0f} | "
                f"v/c Prom: {avg_vc:.2f} | Grado Prom: {avg_degree:.1f}"
            )
            
            if self.show_communities and n_communities > 0:
                legend_text += f" | 🏘️ Comunidades: {n_communities}"
            
            self.legend_label.setText(legend_text)
            
        except Exception as e:
            self.legend_label.setText(f"Error calculando estadísticas: {e}")
