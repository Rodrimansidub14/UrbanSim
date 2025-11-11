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

        self._type_changed = False
        self.HEATMAP_ALIASES = {
            'rent': ('rent', 'avg_rent'),
            'population': ('population', 'pop', 'people'),
            'low_income': ('low_income', 'low_income_share', 'share_low_income', 'discount_low'),
            'gentrification': ('gentrification', 'gentr', 'gentr_index', 'gentr_dispersion'),
        }
        
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
    
    def _pick_spatial_array(self, spatial: dict, kind: str):
        """Return first matching array for the selected kind (considering aliases)."""
        for key in self.HEATMAP_ALIASES.get(kind, (kind,)):
            if key in spatial:
                return np.asarray(spatial[key])
        return None

    def on_heatmap_type_changed(self, text):
        mapping = {
            'Renta': 'rent',
            'Población': 'population',
            'Bajos Ingresos': 'discount_low',
            'Gentrificación': 'gentrification'
        }
        new_type = mapping.get(text, 'rent')
        self._type_changed = (new_type != getattr(self, 'current_heatmap_type', None))
        self.current_heatmap_type = new_type

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
        """Update heatmap based on selected type with aliases and safe fallbacks."""
        spatial = state.get('spatial')
        if not spatial:
            return

        kind = getattr(self, 'current_heatmap_type', 'rent')
        data = self._pick_spatial_array(spatial, kind)

        if data is None:
            # Helpful debug so this doesn't fail silently
            print(f"[heatmap] Missing data for '{kind}'. Available keys: {list(spatial.keys())}")
            return

        # Force a fresh view on type changes; keep incremental updates snappy otherwise
        auto_range = self._type_changed
        self._type_changed = False

        # If your sim mutates arrays in-place, .copy() guarantees a redraw
        self.image_view.setImage(data.T.copy(), autoRange=auto_range, autoLevels=True)
            
    def clear_plots(self):
        """Clear all plot data"""
        for plot_data in self.kpi_plots.values():
            plot_data['x_data'].clear()
            plot_data['y_data'].clear()
            plot_data['curve'].setData([], [])
