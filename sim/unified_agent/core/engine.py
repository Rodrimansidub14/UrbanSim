"""
Core simulation engine that integrates CityModel with StreamServer
Runs in a background thread with async event loop
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
    Unified simulation engine that runs CityModel and StreamServer
    in a background thread with async event loop
    """
    
    # Qt signals for cross-thread communication
    step_completed = pyqtSignal(int)  # Emits step number
    state_updated = pyqtSignal(dict)  # Emits full state
    
    def __init__(self, host="localhost", port=8765, init_settings=None):
        """
        Initialize simulation engine
        
        Args:
            host: WebSocket host
            port: WebSocket port  
            init_settings: Dict with 'grid_size', 'n_households', 'seed', 'max_steps'
        """
        super().__init__()
        
        # Create model with initialization settings
        if init_settings:
            self.model = CityModel(
                grid_size=init_settings.get('grid_size'),
                n_households=init_settings.get('n_households'),
                seed=init_settings.get('seed')
            )
            print(f"🏗️  Model initialized with grid={init_settings.get('grid_size')}x{init_settings.get('grid_size')}, households={init_settings.get('n_households')}")
        else:
            self.model = CityModel()
            print("🏗️  Model initialized with default settings")
            
        self.server = StreamServer(self.model, host=host, port=port)
        self.running = False
        self.paused = True  # START PAUSED - don't run automatically
        self.thread = None
        self.loop = None
        self.step_delay = 0.1  # seconds between steps
        
    async def run_async(self):
        """Async simulation loop"""
        # Start the WebSocket server
        await self.server.start()
        
        # Send initial state safely
        try:
            state = self.server._build_state_message()
            self.state_updated.emit(state)
        except Exception as e:
            print(f"⚠️  Error building initial state: {e}")
        
        while self.running:
            if not self.paused:
                try:
                    # Step the simulation
                    self.model.step_once()
                    
                    # Broadcast to WebSocket clients
                    await self.server.broadcast_tick()
                    
                    # Emit Qt signals for UI update
                    self.step_completed.emit(self.model.step)
                    state = self.server._build_state_message()
                    self.state_updated.emit(state)
                except Exception as e:
                    print(f"❌ Error in simulation step: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Small delay to control simulation speed
            await asyncio.sleep(self.step_delay)
            
        # Cleanup when stopped
        await self.server.stop()
        
    def _run_in_thread(self):
        """Thread target that creates and runs the async event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.run_async())
        
    def start(self):
        """Start the simulation engine in a background thread"""
        if self.running:
            return
            
        self.running = True
        self.paused = False
        self.thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self.thread.start()
        print("🚀 Simulation engine started")
        
    def stop(self):
        """Stop the simulation engine"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        
        # Save results to CSV when stopping
        self.save_results()
        print("🛑 Simulation engine stopped")
        
    def pause(self):
        """Pause the simulation"""
        self.paused = True
        print("⏸️  Simulation paused")
        
    def resume(self):
        """Resume the simulation"""
        self.paused = False
        print("▶️  Simulation resumed")
        
    def set_speed(self, delay: float):
        """Set simulation speed (delay between steps in seconds)"""
        self.step_delay = max(0.001, delay)
        
    def send_command(self, command: dict):
        """Send a command to the simulation (thread-safe)"""
        if self.loop and self.running:
            asyncio.run_coroutine_threadsafe(
                self._process_command(command),
                self.loop
            )
            
    async def _process_command(self, command: dict):
        """Process command in the async loop"""
        import json
        await self.server.process_command(
            json.dumps(command),
            None  # No specific websocket needed for internal commands
        )
    
    def save_results(self):
        """Save simulation results to CSV file"""
        try:
            # Create outputs directory if it doesn't exist
            outputs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'outputs')
            os.makedirs(outputs_dir, exist_ok=True)
            
            # Define the output file path
            output_file = os.path.join(outputs_dir, 'rt_results.csv')
            
            # Check if model has records
            if not self.model.records:
                print("⚠️  No simulation data to save")
                return
            
            # Write records to CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                # Get field names from the first record
                fieldnames = list(self.model.records[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # Write header and data
                writer.writeheader()
                writer.writerows(self.model.records)
            
            print(f"💾 Results saved to: {output_file}")
            print(f"📊 Total steps recorded: {len(self.model.records)}")
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            import traceback
            traceback.print_exc()
