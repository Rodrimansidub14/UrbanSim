"""
Scenario Recorder - Registra todos los cambios paramétricos durante la simulación
Exporta a JSON para análisis posterior y reproducción de escenarios
"""
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Any, Optional


class ScenarioRecorder:
    """
    Registra cambios de parámetros durante la simulación
    con timestamp, step, parámetro, valor y usuario
    """
    
    def __init__(self, path: str = "scenarios.json"):
        self.path = Path(path)
        self.records = []
        self.session_start = datetime.now().isoformat()
        self.session_id = f"session_{int(time.time())}"
        
    def log_change(self, step: int, param: str, value: Any, 
                   user: str = "GUI", notes: str = ""):
        """
        Registra un cambio de parámetro
        
        Args:
            step: Paso de simulación actual
            param: Nombre del parámetro modificado
            value: Nuevo valor del parámetro
            user: Fuente del cambio (GUI, API, Script)
            notes: Notas adicionales
        """
        record = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "parameter": param,
            "value": value,
            "user": user,
            "notes": notes
        }
        self.records.append(record)
        print(f"📝 Scenario recorded: {param} = {value} at step {step}")
        
    def get_scenario_count(self) -> int:
        """Retorna el número de cambios registrados"""
        return len(self.records)
        
    def get_latest_changes(self, n: int = 5) -> list:
        """Retorna los últimos N cambios"""
        return self.records[-n:] if self.records else []
        
    def save(self) -> bool:
        """
        Guarda el registro completo a JSON
        
        Returns:
            True si se guardó exitosamente
        """
        try:
            output = {
                "session_id": self.session_id,
                "session_start": self.session_start,
                "total_changes": len(self.records),
                "changes": self.records
            }
            
            with open(self.path, 'w') as f:
                json.dump(output, f, indent=2)
                
            print(f"✅ Scenario saved to {self.path} ({len(self.records)} changes)")
            return True
            
        except Exception as e:
            print(f"❌ Error saving scenario: {e}")
            return False
            
    def load(self, path: Optional[str] = None) -> bool:
        """
        Carga un escenario desde JSON
        
        Args:
            path: Ruta al archivo (usa self.path si es None)
            
        Returns:
            True si se cargó exitosamente
        """
        load_path = Path(path) if path else self.path
        
        try:
            with open(load_path, 'r') as f:
                data = json.load(f)
                
            self.session_id = data.get("session_id", self.session_id)
            self.session_start = data.get("session_start", self.session_start)
            self.records = data.get("changes", [])
            
            print(f"✅ Scenario loaded from {load_path} ({len(self.records)} changes)")
            return True
            
        except FileNotFoundError:
            print(f"⚠️  No scenario file found at {load_path}")
            return False
        except Exception as e:
            print(f"❌ Error loading scenario: {e}")
            return False
            
    def export_replay_script(self, output_path: str = "replay_scenario.py") -> bool:
        """
        Exporta un script Python para reproducir el escenario
        
        Args:
            output_path: Ruta del script de salida
            
        Returns:
            True si se exportó exitosamente
        """
        try:
            script_lines = [
                "# Auto-generated scenario replay script",
                f"# Session: {self.session_id}",
                f"# Created: {datetime.now().isoformat()}",
                "",
                "import time",
                "from unified_agent.core.engine import SimulationEngine",
                "",
                "# Initialize engine",
                "engine = SimulationEngine()",
                "engine.start()",
                "",
                "# Replay parameter changes",
            ]
            
            for record in self.records:
                step = record['step']
                param = record['parameter']
                value = record['value']
                
                # Wait for correct step
                script_lines.append(f"")
                script_lines.append(f"# Step {step}: {param} = {value}")
                script_lines.append(f"while engine.model.step < {step}:")
                script_lines.append(f"    time.sleep(0.1)")
                
                # Apply change
                script_lines.append(f"engine.send_command({{")
                script_lines.append(f"    'command': 'update_param',")
                script_lines.append(f"    'param': '{param}',")
                script_lines.append(f"    'value': {value}")
                script_lines.append(f"}})")
                
            script_lines.append("")
            script_lines.append("print('✅ Scenario replay complete')")
            
            with open(output_path, 'w') as f:
                f.write('\n'.join(script_lines))
                
            print(f"✅ Replay script exported to {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting replay script: {e}")
            return False
            
    def get_summary(self) -> dict:
        """
        Genera un resumen del escenario
        
        Returns:
            Diccionario con estadísticas del escenario
        """
        if not self.records:
            return {
                "total_changes": 0,
                "parameters_modified": [],
                "steps_range": (0, 0)
            }
            
        params_modified = list(set(r['parameter'] for r in self.records))
        steps = [r['step'] for r in self.records]
        
        return {
            "total_changes": len(self.records),
            "parameters_modified": params_modified,
            "steps_range": (min(steps), max(steps)),
            "session_start": self.session_start,
            "session_id": self.session_id
        }
