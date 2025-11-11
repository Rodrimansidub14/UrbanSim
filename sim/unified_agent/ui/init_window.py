"""
Initialization Settings Window
Permite configurar parámetros globales antes de iniciar la simulación
"""
import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSpinBox, QDoubleSpinBox, QPushButton,
    QGroupBox, QLineEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path


class InitSettingsWindow(QDialog):
    """
    Ventana de configuración inicial de la simulación
    Se muestra antes del inicio para ajustar parámetros globales
    """
    
    # Signal emitted when user confirms settings
    settings_confirmed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎛️ Simulation Initialization Settings")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        # Default settings
        self.settings = {
            'n_households': 4000,
            'grid_size': 10,
            'seed': 42,
            'max_steps': 120,
            'n_developers': 8,
            'init_units_per_neigh': (30, 10),
            'target_occupancy': 0.92,
            'price_adj_alpha': 0.25,
        }
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("⚙️ Configure simulation parameters before starting")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Demographics group
        demo_group = self.create_demographics_group()
        layout.addWidget(demo_group)
        
        # Urban structure group
        urban_group = self.create_urban_structure_group()
        layout.addWidget(urban_group)
        
        # Market parameters group
        market_group = self.create_market_parameters_group()
        layout.addWidget(market_group)
        
        # Simulation control group
        sim_group = self.create_simulation_control_group()
        layout.addWidget(sim_group)
        
        # Buttons
        buttons = self.create_buttons()
        layout.addLayout(buttons)
        
    def create_demographics_group(self) -> QGroupBox:
        """Create demographics configuration group"""
        group = QGroupBox("👥 Demographics")
        form = QFormLayout()
        group.setLayout(form)
        
        # Number of households
        self.households_spin = QSpinBox()
        self.households_spin.setRange(100, 20000)
        self.households_spin.setSingleStep(100)
        self.households_spin.setValue(self.settings['n_households'])
        form.addRow("Total Households:", self.households_spin)
        
        # Income distribution (read-only display)
        income_label = QLabel("Low: 45%, Mid: 40%, High: 15%")
        income_label.setStyleSheet("color: #666;")
        form.addRow("Income Distribution:", income_label)
        
        return group
        
    def create_urban_structure_group(self) -> QGroupBox:
        """Create urban structure configuration group"""
        group = QGroupBox("🏙️ Urban Structure")
        form = QFormLayout()
        group.setLayout(form)
        
        # Grid size
        self.grid_spin = QSpinBox()
        self.grid_spin.setRange(5, 30)
        self.grid_spin.setValue(self.settings['grid_size'])
        form.addRow("Grid Size (N×N):", self.grid_spin)
        
        # Developers
        self.developers_spin = QSpinBox()
        self.developers_spin.setRange(1, 20)
        self.developers_spin.setValue(self.settings['n_developers'])
        form.addRow("Number of Developers:", self.developers_spin)
        
        # Initial units per neighborhood
        units_layout = QHBoxLayout()
        self.market_units_spin = QSpinBox()
        self.market_units_spin.setRange(10, 100)
        self.market_units_spin.setValue(self.settings['init_units_per_neigh'][0])
        self.aff_units_spin = QSpinBox()
        self.aff_units_spin.setRange(0, 50)
        self.aff_units_spin.setValue(self.settings['init_units_per_neigh'][1])
        
        units_layout.addWidget(QLabel("Market:"))
        units_layout.addWidget(self.market_units_spin)
        units_layout.addWidget(QLabel("Affordable:"))
        units_layout.addWidget(self.aff_units_spin)
        form.addRow("Init Units/Neighborhood:", units_layout)
        
        return group
        
    def create_market_parameters_group(self) -> QGroupBox:
        """Create market parameters group"""
        group = QGroupBox("💹 Market Parameters")
        form = QFormLayout()
        group.setLayout(form)
        
        # Target occupancy
        self.occupancy_spin = QDoubleSpinBox()
        self.occupancy_spin.setRange(0.70, 0.99)
        self.occupancy_spin.setSingleStep(0.01)
        self.occupancy_spin.setDecimals(2)
        self.occupancy_spin.setValue(self.settings['target_occupancy'])
        form.addRow("Target Occupancy:", self.occupancy_spin)
        
        # Price adjustment alpha
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.05, 1.0)
        self.alpha_spin.setSingleStep(0.05)
        self.alpha_spin.setDecimals(2)
        self.alpha_spin.setValue(self.settings['price_adj_alpha'])
        form.addRow("Price Adjustment α:", self.alpha_spin)
        
        return group
        
    def create_simulation_control_group(self) -> QGroupBox:
        """Create simulation control group"""
        group = QGroupBox("🎮 Simulation Control")
        form = QFormLayout()
        group.setLayout(form)
        
        # Random seed
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 99999)
        self.seed_spin.setValue(self.settings['seed'])
        form.addRow("Random Seed:", self.seed_spin)
        
        # Max steps
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(10, 1000)
        self.steps_spin.setSingleStep(10)
        self.steps_spin.setValue(self.settings['max_steps'])
        form.addRow("Max Simulation Steps:", self.steps_spin)
        
        return group
        
    def create_buttons(self) -> QHBoxLayout:
        """Create action buttons"""
        layout = QHBoxLayout()
        
        # Load from file
        load_btn = QPushButton("📂 Load Config")
        load_btn.clicked.connect(self.load_config)
        layout.addWidget(load_btn)
        
        # Save to file
        save_btn = QPushButton("💾 Save Config")
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        # Cancel
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # Start simulation
        start_btn = QPushButton("🚀 Start Simulation")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        start_btn.clicked.connect(self.confirm_settings)
        layout.addWidget(start_btn)
        
        return layout
        
    def collect_settings(self) -> dict:
        """Collect all settings from UI"""
        return {
            'n_households': self.households_spin.value(),
            'grid_size': self.grid_spin.value(),
            'seed': self.seed_spin.value(),
            'max_steps': self.steps_spin.value(),
            'n_developers': self.developers_spin.value(),
            'init_units_per_neigh': (
                self.market_units_spin.value(),
                self.aff_units_spin.value()
            ),
            'target_occupancy': self.occupancy_spin.value(),
            'price_adj_alpha': self.alpha_spin.value(),
        }
        
    def confirm_settings(self):
        """Confirm and emit settings"""
        self.settings = self.collect_settings()
        
        # Validation
        if self.settings['n_households'] < 100:
            QMessageBox.warning(self, "Invalid Settings", 
                              "Number of households must be at least 100")
            return
            
        if self.settings['grid_size'] < 5:
            QMessageBox.warning(self, "Invalid Settings",
                              "Grid size must be at least 5×5")
            return
            
        # Emit signal and close
        self.settings_confirmed.emit(self.settings)
        self.accept()
        
    def save_config(self):
        """Save configuration to JSON file"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            "sim_config.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                settings = self.collect_settings()
                with open(filename, 'w') as f:
                    json.dump(settings, f, indent=2)
                QMessageBox.information(self, "Success", 
                                      f"Configuration saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to save configuration: {e}")
                
    def load_config(self):
        """Load configuration from JSON file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Configuration",
            "",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    settings = json.load(f)
                    
                # Update UI with loaded settings
                self.households_spin.setValue(settings.get('n_households', 4000))
                self.grid_spin.setValue(settings.get('grid_size', 10))
                self.seed_spin.setValue(settings.get('seed', 42))
                self.steps_spin.setValue(settings.get('max_steps', 120))
                self.developers_spin.setValue(settings.get('n_developers', 8))
                self.occupancy_spin.setValue(settings.get('target_occupancy', 0.92))
                self.alpha_spin.setValue(settings.get('price_adj_alpha', 0.25))
                
                units = settings.get('init_units_per_neigh', (30, 10))
                self.market_units_spin.setValue(units[0])
                self.aff_units_spin.setValue(units[1])
                
                QMessageBox.information(self, "Success",
                                      f"Configuration loaded from {filename}")
                                      
            except Exception as e:
                QMessageBox.critical(self, "Error",
                                   f"Failed to load configuration: {e}")
