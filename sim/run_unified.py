import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from unified_agent.core import SimulationEngine
from unified_agent.ui import MainWindow
from unified_agent.dash_embedded import start_dash_thread


def main():
    """Punto de entrada principal del agente unificado"""
    print("=" * 70)
    print(" SIMULACIÓN URBANA - AGENTE UNIFICADO")
    print("=" * 70)
    print()
    print("Iniciando el sistema integrado de simulación...")
    print()
    
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Simulación Urbana - Agente Unificado")
    app.setOrganizationName("ModSim")
    
    # 0. Mostrar ventana de configuración inicial
    print(" Abriendo ventana de configuración inicial...")
    from unified_agent.ui.init_window import InitSettingsWindow
    init_window = InitSettingsWindow()
    
    init_settings = None
    
    def on_settings_confirmed(settings):
        nonlocal init_settings
        init_settings = settings
        print(f"Configuración confirmada:")
        print(f"   - Cuadrícula: {settings['grid_size']}×{settings['grid_size']}")
        print(f"   - Hogares: {settings['n_households']}")
        print(f"   - Semilla: {settings['seed']}")
        print(f"   - Pasos Máximos: {settings['max_steps']}")
        
    init_window.settings_confirmed.connect(on_settings_confirmed)
    
    if init_window.exec_() != init_window.Accepted:
        print("Inicialización cancelada por el usuario")
        sys.exit(0)
    
    if init_settings is None:
        print("No se proporcionó configuración")
        sys.exit(1)
    
    # 1. Crear e iniciar el motor de simulación con la configuración inicial
    print("Inicializando motor de simulación...")
    engine = SimulationEngine(host="localhost", port=8765, init_settings=init_settings)
    
    engine.start()
    time.sleep(0.5)  # Darle un momento al motor para iniciar
    
    # 2. Iniciar el servidor Dash en un hilo en segundo plano
    print("Iniciando servidor Dash embebido...")
    dash_thread = start_dash_thread(host="127.0.0.1", port=8050)
    time.sleep(1)  # Darle tiempo a Dash para iniciar
    
    # 3. Crear y mostrar la ventana principal
    print("Creando ventana principal...")
    window = MainWindow(engine, init_settings)
    window.show()
    
    # 4. Cargar el panel Dash después de un breve retraso
    def load_dashboard():
        print("Cargando panel de control (dashboard)...")
        window.right_panel.load_dashboard()
        
    QTimer.singleShot(2000, load_dashboard)  # Cargar después de 2 segundos
    
    print()
    print("=" * 70)
    print("¡AGENTE UNIFICADO LISTO!")
    print("=" * 70)
    print()
    print("Panel Izquierdo:  Analíticas en tiempo real con PyQtGraph")
    print("Panel Derecho:    Panel de control Dash")
    print("Controles:        Barra superior para reproducir/pausar/cambiar velocidad")
    print("Estado:           Barra inferior muestra FPS/CPU/Paso")
    print()
    print("Consejo: Usa los deslizadores en el panel derecho para ajustar políticas")
    print("Consejo: Haz clic en 'Aplicar Cambios' para actualizar parámetros de simulación")
    print()
    print("=" * 70)
    print()
    
    # Ejecutar el ciclo de eventos de Qt
    exit_code = app.exec_()
    
    # Limpieza
    print("\n Cerrando el sistema...")
    engine.stop()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
