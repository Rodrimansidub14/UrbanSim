"""
Thread management utilities for the unified agent
"""
import threading
from typing import Callable


class ManagedThread:
    """Wrapper for managing background threads"""
    
    def __init__(self, target: Callable, name: str = None):
        self.target = target
        self.name = name or "ManagedThread"
        self.thread = None
        self.running = False
        
    def start(self):
        """Start the thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(
            target=self.target,
            name=self.name,
            daemon=True
        )
        self.thread.start()
        print(f"✅ Started thread: {self.name}")
        
    def stop(self, timeout=2):
        """Stop the thread"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)
        print(f"🛑 Stopped thread: {self.name}")
        
    def is_alive(self):
        """Check if thread is alive"""
        return self.thread and self.thread.is_alive()
