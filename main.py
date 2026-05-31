import sys
from PyQt6.QtWidgets import QApplication
from app_config import AppConfig
from vpn_engine import VPNEngine
from ui_main import MainWindow
from theme_manager import ThemeManager

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("OpenVPN Client")
    
    config = AppConfig()
    theme_manager = ThemeManager(config)
    engine = VPNEngine(config)
    
    window = MainWindow(config, engine, theme_manager)
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
