"""
PlanIFlow - Project Planner - Main Entry Point
A desktop project management application similar to Microsoft Project
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QIcon, QPixmap
from ui_main import MainWindow, get_resource_path
from PyQt6.QtCore import Qt, QTimer


def main():
    """Main application entry point"""
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("PlanIFlow - Project Planner")
    app.setOrganizationName("PlanIFlow - Project Planner")
    
    # *** SET APPLICATION ICON ***
    icon_path = get_resource_path('images/logo.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()