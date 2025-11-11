"""
Right panel with embedded Dash dashboard via QWebEngineView
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, pyqtSlot
import time


class RightPanel(QWidget):
    """
    Right panel containing embedded Dash dashboard
    """
    
    def __init__(self, dash_url="http://localhost:8050"):
        super().__init__()
        self.dash_url = dash_url
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Status label
        self.status_label = QLabel("⏳ Loading dashboard...")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.status_label)
        
        # Web view for Dash
        self.webview = QWebEngineView()
        self.webview.loadFinished.connect(self.on_load_finished)
        layout.addWidget(self.webview)
        
    def load_dashboard(self):
        """Load the Dash dashboard"""
        # Wait a moment for Dash server to start
        time.sleep(1)
        self.webview.setUrl(QUrl(self.dash_url))
        
    @pyqtSlot(bool)
    def on_load_finished(self, success):
        """Handle load completion"""
        if success:
            self.status_label.setText("✅ Dashboard loaded")
            self.status_label.setStyleSheet("padding: 5px; background-color: #d4edda; color: #155724;")
        else:
            self.status_label.setText("❌ Failed to load dashboard")
            self.status_label.setStyleSheet("padding: 5px; background-color: #f8d7da; color: #721c24;")
            
    def reload(self):
        """Reload the dashboard"""
        self.webview.reload()
