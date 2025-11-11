"""
Unified Simulation Agent - Single-window interface
Run this to start the complete integrated simulation system

Features:
- CityModel simulation engine (background thread)
- StreamServer WebSocket broadcasting
- PyQtGraph real-time analytics (left panel)
- Dash control dashboard (right panel, embedded)
- Status bar with FPS, CPU, step counter
- Play/Pause/Speed controls

No multiple terminals needed - everything in one window!
"""
import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from unified_agent.core import SimulationEngine
from unified_agent.ui import MainWindow
from unified_agent.dash_embedded import start_dash_thread


def main():
    """Main entry point for the unified agent"""
    print("=" * 70)
    print("🏙️  URBAN SIMULATION - UNIFIED AGENT")
    print("=" * 70)
    print()
    print("Starting integrated simulation system...")
    print()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Urban Simulation - Unified Agent")
    app.setOrganizationName("ModSim")
    
    # 0. Show initialization settings window
    print("0️⃣  Opening initialization settings...")
    from unified_agent.ui.init_window import InitSettingsWindow
    init_window = InitSettingsWindow()
    
    init_settings = None
    
    def on_settings_confirmed(settings):
        nonlocal init_settings
        init_settings = settings
        print(f"✅ Configuration confirmed:")
        print(f"   - Grid: {settings['grid_size']}×{settings['grid_size']}")
        print(f"   - Households: {settings['n_households']}")
        print(f"   - Seed: {settings['seed']}")
        print(f"   - Max Steps: {settings['max_steps']}")
        
    init_window.settings_confirmed.connect(on_settings_confirmed)
    
    if init_window.exec_() != init_window.Accepted:
        print("❌ Initialization cancelled by user")
        sys.exit(0)
    
    if init_settings is None:
        print("❌ No settings provided")
        sys.exit(1)
    
    # 1. Create and start simulation engine with initialization settings
    print("1️⃣  Initializing simulation engine...")
    engine = SimulationEngine(host="localhost", port=8765, init_settings=init_settings)
    
    engine.start()
    time.sleep(0.5)  # Give engine a moment to start
    
    # 2. Start Dash server in background thread
    print("2️⃣  Starting embedded Dash server...")
    dash_thread = start_dash_thread(host="127.0.0.1", port=8050)
    time.sleep(1)  # Give Dash time to start
    
    # 3. Create and show main window
    print("3️⃣  Creating main window...")
    window = MainWindow(engine, init_settings)
    window.show()
    
    # 4. Load Dash dashboard after a short delay
    def load_dashboard():
        print("4️⃣  Loading dashboard...")
        window.right_panel.load_dashboard()
        
    QTimer.singleShot(2000, load_dashboard)  # Load after 2 seconds
    
    print()
    print("=" * 70)
    print("✅ UNIFIED AGENT READY!")
    print("=" * 70)
    print()
    print("📊 Left Panel:  PyQtGraph real-time analytics")
    print("🎛️  Right Panel: Dash control dashboard")
    print("⚙️  Controls:    Top bar for play/pause/speed")
    print("📈 Status:      Bottom bar shows FPS/CPU/Step")
    print()
    print("💡 Tip: Use the sliders in the right panel to adjust policies")
    print("💡 Tip: Click 'Apply Changes' to update simulation parameters")
    print()
    print("=" * 70)
    print()
    
    # Run Qt event loop
    exit_code = app.exec_()
    
    # Cleanup
    print("\n🛑 Shutting down...")
    engine.stop()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
