"""
Unified Agent for Urban Simulation
Integrates CityModel, StreamServer, PyQtGraph, and Dash in a single window
"""
__version__ = "1.0.0"

from .core import SimulationEngine
from .ui import MainWindow
from .dash_embedded import start_dash_thread

__all__ = ['SimulationEngine', 'MainWindow', 'start_dash_thread']
