"""
PlanIFlow - Project Planner - Main Entry Point
A desktop project management application similar to Microsoft Project
"""

import sys
import os
import base64

# Import only essential PyQt6 modules first for fast splash screen
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def main():
    """Main application entry point"""
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("PlanIFlow - Project Planner")
    app.setOrganizationName("PlanIFlow - Project Planner")
    
    # *** SET APPLICATION ICON (BASE64) ***
    from app_images import SPLASH_BASE64, LOGO_ICO_BASE64
    
    icon_bytes = base64.b64decode(LOGO_ICO_BASE64)
    icon_pix = QPixmap()
    icon_pix.loadFromData(icon_bytes)
    if not icon_pix.isNull():
        app.setWindowIcon(QIcon(icon_pix))
    
    # *** SHOW SPLASH SCREEN IMMEDIATELY (BASE64) ***
    splash_bytes = base64.b64decode(SPLASH_BASE64)
    splash_pix = QPixmap()
    splash_pix.loadFromData(splash_bytes)
    splash = None
    
    # Use the custom splash screen with loading message below
    if not splash_pix.isNull():
        splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
        # Add "Loading..." message below the splash image
        splash.showMessage("PlanIFlow 1.5 Loading...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.darkGray)
        splash.show()
        app.processEvents()  # Ensure splash is drawn immediately
    
    # NOW import heavy modules while splash is visible
    from ui_main import MainWindow
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Close splash screen
    if splash:
        splash.finish(window)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()