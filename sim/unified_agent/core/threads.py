"""
Utilidades para la gestión de hilos del agente unificado
"""
import threading
from typing import Callable


class ManagedThread:
    """Contenedor para gestionar hilos en segundo plano"""
    
    def __init__(self, target: Callable, name: str = None):
        self.target = target
        self.name = name or "ManagedThread"
        self.thread = None
        self.running = False
        
    def start(self):
        """Iniciar el hilo"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(
            target=self.target,
            name=self.name,
            daemon=True
        )
        self.thread.start()
        print(f"Hilo iniciado: {self.name}")
        
    def stop(self, timeout=2):
        """Detener el hilo"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)
        print(f"Hilo detenido: {self.name}")
        
    def is_alive(self):
        """Verificar si el hilo está activo"""
        return self.thread and self.thread.is_alive()
