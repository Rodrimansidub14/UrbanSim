"""
Main window for the unified simulation agent
Combines PyQtGraph analytics (left) with Dash dashboard (right)
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QMenuBar, QAction, QLabel,
    QPushButton, QSlider
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QPalette, QColor
from .left_panel import LeftPanel
from .right_panel import RightPanel
from .params_panel import ParamsPanel
from ..utils.scenario_recorder import ScenarioRecorder
from ..utils.sanity_checks import SanityChecker
import psutil
import time


class MainWindow(QMainWindow):
    """
    Unified main window containing all simulation components
    """
    
    def __init__(self, engine, init_settings: dict = None):
        super().__init__()
        self.engine = engine
        self.init_settings = init_settings or {}
        self.start_time = time.time()
        self.frame_count = 0
        self.fps = 0
        
        # Initialize utilities
        self.recorder = ScenarioRecorder()
        self.sanity_checker = SanityChecker()
        
        # Connect engine signals
        self.engine.step_completed.connect(self.on_step_completed)
        self.engine.state_updated.connect(self.on_state_updated)
        
        self.init_ui()
        self.setup_menu()
        self.setup_statusbar()
        self.setup_timers()
        
    def init_ui(self):
        """Inicializar la interfaz de usuario"""
        self.setWindowTitle("🏙️ Simulación Urbana - Agente Unificado")
        self.setGeometry(100, 100, 1600, 900)
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Control bar at top
        control_bar = self.create_control_bar()
        layout.addWidget(control_bar)
        
        # Main splitter: Params | PyQtGraph | Dash
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left: Parameter controls
        self.params_panel = ParamsPanel()
        self.params_panel.params_changed.connect(self.on_params_changed)
        main_splitter.addWidget(self.params_panel)
        
        # Center: PyQtGraph analytics
        self.left_panel = LeftPanel()
        main_splitter.addWidget(self.left_panel)
        
        # Right: Dash dashboard
        self.right_panel = RightPanel()
        main_splitter.addWidget(self.right_panel)
        
        # Set initial sizes (15% params, 45% pyqt, 40% dash)
        main_splitter.setSizes([240, 720, 640])
        layout.addWidget(main_splitter)
        
    def create_control_bar(self):
        """Crear barra de control con controles de simulación"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f8f9fa; padding: 5px;")
        layout = QHBoxLayout()
        widget.setLayout(layout)
        
        # Botón Play/Pausa (inicia como Play ya que la simulación inicia pausada)
        self.play_pause_btn = QPushButton("▶️ Iniciar")
        self.play_pause_btn.clicked.connect(self.toggle_pause)
        layout.addWidget(self.play_pause_btn)
        
        # Botón Reset
        reset_btn = QPushButton("🔄 Reiniciar Vista")
        reset_btn.clicked.connect(self.reset_view)
        layout.addWidget(reset_btn)
        
        # Botón Exportar
        export_btn = QPushButton("💾 Exportar Gráficas")
        export_btn.clicked.connect(self.export_visualizations)
        export_btn.setToolTip("Guardar todas las gráficas y grafos actuales")
        layout.addWidget(export_btn)
        
        # Control de velocidad
        layout.addWidget(QLabel("Velocidad:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(20)
        self.speed_slider.setValue(10)
        self.speed_slider.setFixedWidth(150)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        layout.addWidget(self.speed_slider)
        self.speed_label = QLabel("1.0x")
        layout.addWidget(self.speed_label)
        
        layout.addStretch()
        
        # Indicador de estado (inicia como Pausado)
        self.status_indicator = QLabel("⏸️ Pausado")
        self.status_indicator.setStyleSheet("font-weight: bold; color: orange;")
        layout.addWidget(self.status_indicator)
        
        return widget
        
    def setup_menu(self):
        """Configurar barra de menú"""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu("&Archivo")
        
        exit_action = QAction("&Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Vista
        view_menu = menubar.addMenu("&Vista")
        
        reload_dash = QAction("Recargar Panel", self)
        reload_dash.setShortcut("F5")
        reload_dash.triggered.connect(lambda: self.right_panel.reload())
        view_menu.addAction(reload_dash)
        
        clear_plots = QAction("Limpiar Gráficos", self)
        clear_plots.triggered.connect(lambda: self.left_panel.clear_plots())
        view_menu.addAction(clear_plots)
        
    def setup_statusbar(self):
        """Configurar barra de estado"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # Etiquetas de barra de estado
        self.step_label = QLabel("Paso: 0")
        self.fps_label = QLabel("FPS: 0")
        self.cpu_label = QLabel("CPU: 0%")
        self.elapsed_label = QLabel("Tiempo: 0:00")
        
        # Indicador de verificación de integridad
        self.sanity_indicator = QLabel("🟢 OK")
        self.sanity_indicator.setToolTip("Verificaciones de integridad del sistema")
        
        # Contador de escenarios
        self.scenario_counter = QLabel("📝 Escenarios: 0")
        self.scenario_counter.setToolTip("Número de cambios de parámetros registrados")
        
        self.statusbar.addWidget(self.sanity_indicator)
        self.statusbar.addWidget(self.scenario_counter)
        self.statusbar.addPermanentWidget(self.step_label)
        self.statusbar.addPermanentWidget(self.fps_label)
        self.statusbar.addPermanentWidget(self.cpu_label)
        self.statusbar.addPermanentWidget(self.elapsed_label)
        
    def setup_timers(self):
        """Setup update timers"""
        # FPS/CPU monitor timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_monitors)
        self.monitor_timer.start(1000)  # Update every second
        
    def toggle_pause(self):
        """Toggle simulation pause"""
        if self.engine.paused:
            self.engine.resume()
            self.play_pause_btn.setText("⏸️ Pausar")
            self.status_indicator.setText("🟢 Ejecutando")
            self.status_indicator.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.engine.pause()
            self.play_pause_btn.setText("▶️ Iniciar")
            self.status_indicator.setText("⏸️ Pausado")
            self.status_indicator.setStyleSheet("font-weight: bold; color: orange;")
            
    def reset_view(self):
        """Reset plot views"""
        self.left_panel.clear_plots()
        
    def on_speed_changed(self, value):
        """Handle speed slider change"""
        # Convert slider value to delay (inverse relationship)
        # value 1-20 → delay 0.5-0.01 seconds
        delay = 0.5 / value
        self.engine.set_speed(delay)
        speed_mult = value / 10.0
        self.speed_label.setText(f"{speed_mult:.1f}x")
        
    @pyqtSlot(int)
    def on_step_completed(self, step):
        """Manejar finalización de paso de simulación"""
        self.step_label.setText(f"Paso: {step}")
        self.frame_count += 1
        
    @pyqtSlot(dict)
    def on_state_updated(self, state):
        """Handle state update from engine"""
        # Update left panel plots
        self.left_panel.update_plots(state)
        
        # Run sanity checks
        check_results = self.sanity_checker.run_all_checks(state)
        overall_status = self.sanity_checker.get_overall_status(check_results)
        
        # Update sanity indicator
        status_icons = {
            'green': '🟢 OK',
            'yellow': '🟡 Warning',
            'red': '🔴 Critical'
        }
        self.sanity_indicator.setText(status_icons.get(overall_status, '⚪ Unknown'))
        
        # Set tooltip with alerts
        alerts = self.sanity_checker.get_alerts(check_results)
        if alerts:
            self.sanity_indicator.setToolTip('\n'.join(alerts))
        else:
            self.sanity_indicator.setToolTip('All systems nominal')
        
    def on_params_changed(self, params: dict):
        """Handle parameter changes from UI"""
        print(f"📊 Parameters updated: {params}")
        
        current_step = self.engine.model.step if hasattr(self.engine, 'model') else 0
        
        # Record changes in scenario recorder
        for param_name, value in params.items():
            self.recorder.log_change(
                step=current_step,
                param=param_name,
                value=value,
                user="GUI",
                notes="User adjusted parameter via PyQt panel"
            )
            
            # Send to simulation engine
            self.engine.send_command({
                "command": "update_param",
                "param": param_name,
                "value": value
            })
        
        # Update scenario counter
        self.scenario_counter.setText(f"📝 Scenarios: {self.recorder.get_scenario_count()}")
        
    def update_monitors(self):
        """Update FPS and CPU monitors"""
        # Calculate FPS
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            self.fps = self.frame_count / elapsed
            self.fps_label.setText(f"FPS: {self.fps:.1f}")
            
        # Reset counters every 10 seconds
        if elapsed > 10:
            self.start_time = time.time()
            self.frame_count = 0
            
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_label.setText(f"CPU: {cpu_percent:.0f}%")
        
        # Elapsed time
        total_elapsed = int(elapsed)
        mins = total_elapsed // 60
        secs = total_elapsed % 60
        self.elapsed_label.setText(f"Time: {mins}:{secs:02d}")
    
    def export_visualizations(self):
        """Export all current visualizations to files"""
        from PyQt5.QtWidgets import QMessageBox
        try:
            print("📸 Exporting visualizations...")
            
            # Pause simulation during export
            was_paused = self.engine.paused
            if not was_paused:
                self.engine.pause()
            
            # Export from engine
            run_dir = self.engine.export_all_visualizations()
            
            # Resume if it was running
            if not was_paused:
                self.engine.resume()
            
            if run_dir:
                QMessageBox.information(
                    self,
                    "✅ Exportación Exitosa",
                    f"Todas las gráficas y grafos han sido guardados en:\n\n{run_dir}\n\n"
                    f"Archivos exportados:\n"
                    f"• results.csv - Datos de la simulación\n"
                    f"• time_series.png - Series temporales\n"
                    f"• time_series_housing.png - Gráficas de vivienda\n"
                    f"• map_*.png - Mapas espaciales\n"
                    f"• network_graph_*.png - Grafo de red"
                )
                print(f"✅ Visualizations exported to: {run_dir}")
            else:
                QMessageBox.warning(
                    self,
                    "⚠️ Exportación Incompleta",
                    "La exportación se completó parcialmente. Revisa la consola para más detalles."
                )
                
        except Exception as e:
            print(f"❌ Error during export: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "❌ Error de Exportación",
                f"Ocurrió un error al exportar las visualizaciones:\n\n{str(e)}"
            )
        
    def closeEvent(self, event):
        """Handle window close"""
        print("\n🛑 Shutting down unified agent...")
        
        # Save scenario recording
        if self.recorder.get_scenario_count() > 0:
            print(f"💾 Saving {self.recorder.get_scenario_count()} recorded changes...")
            self.recorder.save()
            self.recorder.export_replay_script()
        
        self.engine.stop()
        event.accept()
