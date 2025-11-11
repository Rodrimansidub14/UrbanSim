"""
Left panel with PyQtGraph analytics and plots
"""
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QComboBox
from PyQt5.QtCore import pyqtSlot
from collections import deque
import numpy as np


class LeftPanel(QWidget):
    """
    Left panel containing PyQtGraph plots for real-time analytics
    """
    
    def __init__(self):
        super().__init__()
        self.max_points = 500
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Crear widget de pestañas
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Pestaña 1: KPIs Series de Tiempo
        self.kpi_widget = self.create_kpi_plots()
        self.tabs.addTab(self.kpi_widget, "📊 Indicadores")
        
        # Pestaña 2: Mapa de Calor
        self.heatmap_widget = self.create_heatmap()
        self.tabs.addTab(self.heatmap_widget, "🗺️ Mapa Calor")
        
        # Pestaña 3: Red
        from .network_panel import NetworkPanel
        self.network_widget = NetworkPanel()
        self.tabs.addTab(self.network_widget, "🕸️ Red")
        
    def create_kpi_plots(self):
        """Create KPI time series plots"""
        widget = pg.GraphicsLayoutWidget()
        widget.setBackground('w')
        
        # Crear 6 gráficos (grid 3x2)
        self.kpi_plots = {}
        kpi_configs = [
            ('avg_rent', 'Renta Promedio', '$/mes', 'b'),
            ('avg_travel', 'Tiempo de Viaje', 'minutos', 'g'),
            ('displacements', 'Desplazamientos', 'hogares', 'r'),
            ('share_low_income', 'Bajos Ingresos %', 'proporción', 'c'),
            ('gentr_dispersion', 'Gentrificación', 'índice', 'm'),
            ('vacancy_rate', 'Tasa Vacancia', 'proporción', 'y'),
        ]
        
        for i, (key, title, ylabel, color) in enumerate(kpi_configs):
            row = i // 2
            col = i % 2
            
            plot = widget.addPlot(row=row, col=col)
            plot.setTitle(title, size='10pt')
            plot.setLabel('left', ylabel, size='8pt')
            plot.setLabel('bottom', 'Paso', size='8pt')
            plot.showGrid(x=True, y=True, alpha=0.3)
            
            self.kpi_plots[key] = {
                'widget': plot,
                'curve': plot.plot(pen=pg.mkPen(color=color, width=2)),
                'x_data': deque(maxlen=self.max_points),
                'y_data': deque(maxlen=self.max_points),
            }
            
        return widget
        
    def create_heatmap(self):
        """Create spatial heatmap"""
        from PyQt5.QtWidgets import QLabel, QComboBox
        
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Selector para tipo de mapa de calor
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Mostrar:"))
        self.heatmap_selector = QComboBox()
        self.heatmap_selector.addItems([
            'Renta', 'Población', 'Bajos Ingresos', 'Gentrificación'
        ])
        self.heatmap_selector.currentTextChanged.connect(self.on_heatmap_type_changed)
        selector_layout.addWidget(self.heatmap_selector)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Create ImageView for heatmap
        self.image_view = pg.ImageView()
        self.image_view.ui.roiBtn.hide()
        self.image_view.ui.menuBtn.hide()
        layout.addWidget(self.image_view)
        
        # Initialize with zeros
        self.heatmap_data = np.zeros((10, 10))
        self.current_heatmap_type = 'rent'
        self.last_state = None
        
        # Set colormap
        cmap = pg.colormap.get('viridis')
        self.image_view.setColorMap(cmap)
        
        return widget
    
    def on_heatmap_type_changed(self, text):
        """Manejar cambio de selección de tipo de mapa de calor"""
        mapping = {
            'Renta': 'rent',
            'Población': 'population',
            'Bajos Ingresos': 'low_income',
            'Gentrificación': 'gentrification'
        }
        self.current_heatmap_type = mapping.get(text, 'rent')
        
        # Re-render with last state if available
        if self.last_state:
            self.update_heatmap(self.last_state)
        
    @pyqtSlot(dict)
    def update_plots(self, state: dict):
        """Update all plots with new state data"""
        if 'kpis' not in state:
            return
        
        self.last_state = state
        kpis = state['kpis']
        step = state.get('step', 0)
        
        # Update time series
        for key, plot_data in self.kpi_plots.items():
            if key in kpis:
                value = kpis[key]
                plot_data['x_data'].append(step)
                plot_data['y_data'].append(value)
                
                x = np.array(plot_data['x_data'])
                y = np.array(plot_data['y_data'])
                plot_data['curve'].setData(x, y)
        
        # Update heatmap
        self.update_heatmap(state)
        
        # Update network
        self.network_widget.update_network(state)
    
    def update_heatmap(self, state: dict):
        """Update heatmap based on selected type"""
        if 'spatial' not in state:
            return
        
        spatial = state['spatial']
        
        # Get the appropriate data based on selection
        if self.current_heatmap_type == 'rent' and 'rent' in spatial:
            data = np.array(spatial['rent'])
        elif self.current_heatmap_type == 'population' and 'population' in spatial:
            data = np.array(spatial['population'])
        elif self.current_heatmap_type == 'low_income' and 'low_income' in spatial:
            data = np.array(spatial['low_income'])
        elif self.current_heatmap_type == 'gentrification' and 'gentrification' in spatial:
            data = np.array(spatial['gentrification'])
        else:
            return
        
        # Update image with proper scaling
        if data.size > 0:
            self.image_view.setImage(data.T, autoRange=False, autoLevels=True)
            
    def clear_plots(self):
        """Clear all plot data"""
        for plot_data in self.kpi_plots.values():
            plot_data['x_data'].clear()
            plot_data['y_data'].clear()
            plot_data['curve'].setData([], [])
