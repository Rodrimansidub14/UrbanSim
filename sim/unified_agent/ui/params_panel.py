"""
Panel de control de parámetros con sliders sincronizados
Incluye parámetros de mercado, demografía, transporte y comportamiento
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QPushButton, QGroupBox, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal


class ParamsPanel(QWidget):
    """
    Panel con sliders de parámetros
    Emite señal cuando los parámetros cambian
    """
    
    # Señal emitida cuando el usuario aplica cambios de parámetros
    params_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.params = {
            # Parámetros de política
            'rent_cap': 0.03,
            'aff_share': 0.3,
            'voucher_discount': 0.0,
            
            # Parámetros de mercado
            'alpha_rent': 0.15,
            'target_occupancy': 0.90,
            'dev_cost': 200000,
            'build_rate': 20,
            
            # Parámetros demográficos
            'net_migration': 0.00,
            'mobility_rate': 0.15,
            
            # Parámetros de transporte
            'road_capacity_mult': 1.0,
            't0_mult': 1.0,
            
            # Parámetros de comportamiento
            'lambda_rent': 0.5,
            'mu_travel': 0.3,
            'gamma_amenities': 0.2
        }
        self.init_ui()
        
    def init_ui(self):
        """Inicializar componentes de interfaz"""
        # Scroll area para todos los parámetros
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        layout = QVBoxLayout()
        scroll_widget.setLayout(layout)
        scroll.setWidget(scroll_widget)
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(scroll)
        
        # === POLÍTICAS ===
        policy_group = QGroupBox("🏛️ Políticas")
        policy_layout = QVBoxLayout()
        policy_group.setLayout(policy_layout)
        layout.addWidget(policy_group)
        
        self.rent_cap_slider, self.rent_cap_label = self.create_slider_row(
            policy_layout, "Control de Renta (mensual):", 0, 50, 30, 5, 
            lambda v: f"{v/1000:.3f}"
        )
        
        self.aff_share_slider, self.aff_share_label = self.create_slider_row(
            policy_layout, "Cuota Vivienda Asequible:", 0, 100, 30, 5,
            lambda v: f"{v}%"
        )
        
        self.voucher_slider, self.voucher_label = self.create_slider_row(
            policy_layout, "Descuento por Voucher:", 0, 50, 0, 5,
            lambda v: f"{v}%"
        )
        
        # === MERCADO ===
        market_group = QGroupBox("📈 Mercado")
        market_layout = QVBoxLayout()
        market_group.setLayout(market_layout)
        layout.addWidget(market_group)
        
        self.alpha_slider, self.alpha_label = self.create_slider_row(
            market_layout, "α (ajuste de precio):", 5, 50, 15, 5,
            lambda v: f"{v/100:.2f}"
        )
        
        self.target_occ_slider, self.target_occ_label = self.create_slider_row(
            market_layout, "Ocupación objetivo:", 85, 97, 90, 1,
            lambda v: f"{v}%"
        )
        
        self.dev_cost_slider, self.dev_cost_label = self.create_slider_row(
            market_layout, "Costo desarrollo (k$):", 100, 500, 200, 50,
            lambda v: f"${v}k"
        )
        
        self.build_rate_slider, self.build_rate_label = self.create_slider_row(
            market_layout, "Tasa construcción (unid/step):", 5, 60, 20, 5,
            lambda v: f"{v}"
        )
        
        # === DEMOGRAFÍA ===
        demo_group = QGroupBox("👥 Demografía")
        demo_layout = QVBoxLayout()
        demo_group.setLayout(demo_layout)
        layout.addWidget(demo_group)
        
        self.migration_slider, self.migration_label = self.create_slider_row(
            demo_layout, "Migración neta:", -20, 20, 0, 5,
            lambda v: f"{v/10:.1f}%"
        )
        
        self.mobility_slider, self.mobility_label = self.create_slider_row(
            demo_layout, "Tasa movilidad:", 5, 30, 15, 5,
            lambda v: f"{v}%"
        )
        
        # === TRANSPORTE ===
        transport_group = QGroupBox("🚗 Transporte")
        transport_layout = QVBoxLayout()
        transport_group.setLayout(transport_layout)
        layout.addWidget(transport_group)
        
        self.road_cap_slider, self.road_cap_label = self.create_slider_row(
            transport_layout, "Capacidad vial (mult.):", 70, 150, 100, 10,
            lambda v: f"{v/100:.2f}x"
        )
        
        self.t0_slider, self.t0_label = self.create_slider_row(
            transport_layout, "Tiempo base (mult.):", 50, 200, 100, 10,
            lambda v: f"{v/100:.2f}x"
        )
        
        # === COMPORTAMIENTO ===
        behavior_group = QGroupBox("🧠 Comportamiento")
        behavior_layout = QVBoxLayout()
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        self.lambda_slider, self.lambda_label = self.create_slider_row(
            behavior_layout, "λ (peso renta):", 0, 100, 50, 10,
            lambda v: f"{v/100:.2f}"
        )
        
        self.mu_slider, self.mu_label = self.create_slider_row(
            behavior_layout, "μ (peso viaje):", 0, 100, 30, 10,
            lambda v: f"{v/100:.2f}"
        )
        
        self.gamma_slider, self.gamma_label = self.create_slider_row(
            behavior_layout, "γ (peso amenidades):", 0, 100, 20, 10,
            lambda v: f"{v/100:.2f}"
        )
        
        # Botón de aplicar
        apply_btn = QPushButton("📤 Aplicar Cambios")
        apply_btn.clicked.connect(self.apply_params)
        apply_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        layout.addWidget(apply_btn)
        
        layout.addStretch()
        
    def create_slider_row(self, parent_layout, label_text, min_val, max_val, default, tick_interval, format_func):
        """Crear una fila con slider y etiqueta"""
        parent_layout.addWidget(QLabel(label_text))
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(tick_interval)
        
        value_label = QLabel(format_func(default))
        value_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        
        slider.valueChanged.connect(lambda v: value_label.setText(format_func(v)))
        
        parent_layout.addWidget(slider)
        parent_layout.addWidget(value_label)
        
        return slider, value_label
        
    def apply_params(self):
        """Recolectar valores actuales de parámetros y emitir señal"""
        self.params = {
            # Políticas
            'rent_cap': self.rent_cap_slider.value() / 1000.0,
            'aff_share': self.aff_share_slider.value() / 100.0,
            'voucher_discount': self.voucher_slider.value() / 100.0,
            
            # Mercado
            'alpha_rent': self.alpha_slider.value() / 100.0,
            'target_occupancy': self.target_occ_slider.value() / 100.0,
            'dev_cost': self.dev_cost_slider.value() * 1000,
            'build_rate': self.build_rate_slider.value(),
            
            # Demografía
            'net_migration': self.migration_slider.value() / 1000.0,
            'mobility_rate': self.mobility_slider.value() / 100.0,
            
            # Transporte
            'road_capacity_mult': self.road_cap_slider.value() / 100.0,
            't0_mult': self.t0_slider.value() / 100.0,
            
            # Comportamiento
            'lambda_rent': self.lambda_slider.value() / 100.0,
            'mu_travel': self.mu_slider.value() / 100.0,
            'gamma_amenities': self.gamma_slider.value() / 100.0
        }
        self.params_changed.emit(self.params)
        print(f"✅ Parámetros aplicados: {len(self.params)} parámetros actualizados")
        
    def set_params(self, params: dict):
        """Actualizar sliders desde fuente externa (para sincronización)"""
        sliders = {
            'rent_cap': (self.rent_cap_slider, 1000),
            'aff_share': (self.aff_share_slider, 100),
            'voucher_discount': (self.voucher_slider, 100),
            'alpha_rent': (self.alpha_slider, 100),
            'target_occupancy': (self.target_occ_slider, 100),
            'dev_cost': (self.dev_cost_slider, 0.001),
            'build_rate': (self.build_rate_slider, 1),
            'net_migration': (self.migration_slider, 1000),
            'mobility_rate': (self.mobility_slider, 100),
            'road_capacity_mult': (self.road_cap_slider, 100),
            't0_mult': (self.t0_slider, 100),
            'lambda_rent': (self.lambda_slider, 100),
            'mu_travel': (self.mu_slider, 100),
            'gamma_amenities': (self.gamma_slider, 100)
        }
        
        for key, (slider, multiplier) in sliders.items():
            if key in params:
                slider.blockSignals(True)
                slider.setValue(int(params[key] * multiplier))
                slider.blockSignals(False)
