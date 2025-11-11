"""
Advanced Parameters Panel
Expone parámetros estructurales, demográficos, de transporte y comportamiento
con rangos seguros y tooltips explicativos
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QGroupBox, QScrollArea, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal


class AdvancedParamsPanel(QWidget):
    """
    Panel con parámetros avanzados del modelo
    Categorizados por tipo: Mercado, Demografía, Transporte, Comportamiento, Política
    """
    
    params_changed = pyqtSignal(dict)
    
    # Parameter definitions with ranges and tooltips
    PARAM_DEFS = {
        # Market parameters
        'alpha_rent': {
            'label': 'Rent Adjustment Speed (α)',
            'range': (0.05, 0.5),
            'default': 0.25,
            'step': 0.01,
            'tooltip': '↑ → Rents react faster to vacancy changes',
            'group': 'Market'
        },
        'target_occupancy': {
            'label': 'Target Occupancy',
            'range': (0.85, 0.97),
            'default': 0.92,
            'step': 0.01,
            'tooltip': '↑ → Higher rents to reduce vacancy',
            'group': 'Market'
        },
        'dev_cost': {
            'label': 'Construction Cost',
            'range': (200, 600),
            'default': 350,
            'step': 10,
            'tooltip': '↑ → Less supply, higher rents',
            'group': 'Market'
        },
        'build_rate': {
            'label': 'Build Rate (units/decision)',
            'range': (5, 60),
            'default': 30,
            'step': 5,
            'tooltip': '↑ → More initial vacancy',
            'group': 'Market'
        },
        
        # Demographics
        'net_migration': {
            'label': 'Net Migration Rate (%)',
            'range': (-2.0, 2.0),
            'default': 0.0,
            'step': 0.1,
            'tooltip': '↑ → More demand pressure',
            'group': 'Demographics'
        },
        'mobility_rate': {
            'label': 'Income Mobility Rate',
            'range': (0.0, 0.01),
            'default': 0.002,
            'step': 0.001,
            'tooltip': '↑ → More class transitions',
            'group': 'Demographics'
        },
        
        # Transport
        'road_capacity_mult': {
            'label': 'Road Capacity Multiplier',
            'range': (0.7, 1.5),
            'default': 1.0,
            'step': 0.05,
            'tooltip': '↑ → Lower travel times',
            'group': 'Transport'
        },
        't0_mult': {
            'label': 'Free-Flow Time Multiplier',
            'range': (0.8, 1.2),
            'default': 1.0,
            'step': 0.05,
            'tooltip': '↓ → Better accessibility',
            'group': 'Transport'
        },
        'incident_rate': {
            'label': 'Incident Rate (λ)',
            'range': (0.0, 0.2),
            'default': 0.0,
            'step': 0.01,
            'tooltip': '↑ → Random travel time spikes',
            'group': 'Transport'
        },
        
        # Behavior
        'lambda_rent': {
            'label': 'Rent Sensitivity (λ)',
            'range': (0.5, 3.0),
            'default': 2.0,
            'step': 0.1,
            'tooltip': '↑ → More sensitive to rent burden',
            'group': 'Behavior'
        },
        'mu_travel': {
            'label': 'Travel Time Value (μ)',
            'range': (0.01, 0.2),
            'default': 0.05,
            'step': 0.01,
            'tooltip': '↑ → Travel time weighs more',
            'group': 'Behavior'
        },
        'gamma_amenities': {
            'label': 'Amenity Preference (γ)',
            'range': (0.0, 2.5),
            'default': 1.2,
            'step': 0.1,
            'tooltip': '↑ → Polarization by amenities',
            'group': 'Behavior'
        },
        'moving_threshold': {
            'label': 'Moving Threshold',
            'range': (0.0, 0.3),
            'default': 0.01,
            'step': 0.01,
            'tooltip': '↑ → Less household mobility',
            'group': 'Behavior'
        },
    }
    
    def __init__(self):
        super().__init__()
        self.param_widgets = {}
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI components"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Title
        title = QLabel("⚙️ Advanced Parameters")
        title.setStyleSheet("font-size: 11pt; font-weight: bold; padding: 5px;")
        main_layout.addWidget(title)
        
        # Scrollable area for parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        
        # Group parameters by category
        groups = {}
        for param_id, param_def in self.PARAM_DEFS.items():
            group_name = param_def['group']
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append((param_id, param_def))
        
        # Create a group box for each category
        for group_name in ['Market', 'Demographics', 'Transport', 'Behavior']:
            if group_name in groups:
                group_box = self.create_param_group(group_name, groups[group_name])
                layout.addWidget(group_box)
        
        # Apply button
        apply_btn = QPushButton("📤 Apply Advanced Parameters")
        apply_btn.clicked.connect(self.apply_params)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
    def create_param_group(self, group_name: str, params: list) -> QGroupBox:
        """Create a group box for a category of parameters"""
        group = QGroupBox(group_name)
        layout = QVBoxLayout()
        group.setLayout(layout)
        
        for param_id, param_def in params:
            param_widget = self.create_param_control(param_id, param_def)
            layout.addWidget(param_widget)
            
        return group
        
    def create_param_control(self, param_id: str, param_def: dict) -> QWidget:
        """Create a control for a single parameter"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Label with tooltip
        label = QLabel(param_def['label'])
        label.setToolTip(param_def['tooltip'])
        layout.addWidget(label)
        
        # Horizontal layout for spinbox and value label
        h_layout = QHBoxLayout()
        
        # Spinbox
        spinbox = QDoubleSpinBox()
        spinbox.setRange(param_def['range'][0], param_def['range'][1])
        spinbox.setSingleStep(param_def['step'])
        spinbox.setValue(param_def['default'])
        spinbox.setDecimals(3 if param_def['step'] < 0.01 else 2)
        spinbox.setToolTip(param_def['tooltip'])
        
        h_layout.addWidget(spinbox)
        
        # Current value label
        value_label = QLabel(f"{param_def['default']:.3f}")
        value_label.setStyleSheet("font-weight: bold; color: #007bff;")
        h_layout.addWidget(value_label)
        
        spinbox.valueChanged.connect(
            lambda v: value_label.setText(f"{v:.3f}")
        )
        
        layout.addLayout(h_layout)
        
        # Store reference
        self.param_widgets[param_id] = {
            'spinbox': spinbox,
            'label': value_label,
            'def': param_def
        }
        
        return widget
        
    def apply_params(self):
        """Collect and emit all parameter values"""
        params = {}
        for param_id, widgets in self.param_widgets.items():
            params[param_id] = widgets['spinbox'].value()
            
        print(f"📊 Advanced parameters: {len(params)} values changed")
        self.params_changed.emit(params)
        
    def set_param(self, param_id: str, value: float):
        """Update a parameter value (for external sync)"""
        if param_id in self.param_widgets:
            spinbox = self.param_widgets[param_id]['spinbox']
            spinbox.blockSignals(True)
            spinbox.setValue(value)
            spinbox.blockSignals(False)
