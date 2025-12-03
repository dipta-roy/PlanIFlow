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
from constants.constants import APP_NAME, VERSION


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

    # Fix for Windows taskbar icon
    if os.name == 'nt':
        import ctypes
        myappid = f'{APP_NAME.lower().replace(" ", "")}.projectplanner.{VERSION}' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QApplication(sys.argv)
    app.setApplicationName(f"{APP_NAME} - Project Planner")
    app.setOrganizationName(f"{APP_NAME} - Project Planner")
    
    # *** SET APPLICATION ICON (BASE64) ***
    from constants.app_images import SPLASH_BASE64, LOGO_ICO_BASE64
    import tempfile
    
    # Create icon from base64 ICO data - save to temp file to preserve all icon sizes
    icon_bytes = base64.b64decode(LOGO_ICO_BASE64)
    
    # Create temp file for the icon
    temp_icon_fd, temp_icon_path = tempfile.mkstemp(suffix='.ico')
    try:
        os.write(temp_icon_fd, icon_bytes)
        os.close(temp_icon_fd)
        
        # Load icon from temp file (preserves all sizes in .ico)
        app_icon = QIcon()
        app_icon.addFile(temp_icon_path)
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)
    finally:
        # Clean up temp file
        try:
            if os.path.exists(temp_icon_path):
                os.remove(temp_icon_path)
        except:
            pass  # Ignore cleanup errors
    
    # *** SHOW SPLASH SCREEN IMMEDIATELY (BASE64) ***
    splash_bytes = base64.b64decode(SPLASH_BASE64)
    splash_pix = QPixmap()
    splash_pix.loadFromData(splash_bytes)
    splash = None
    
    # Use the custom splash screen with loading message below
    if not splash_pix.isNull():
        splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
        # Add "Loading..." message below the splash image
        splash.showMessage(f"{APP_NAME} {VERSION} Loading...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.darkGray)
        splash.show()
        app.processEvents()  # Ensure splash is drawn immediately
    
    # NOW import heavy modules while splash is visible
    from ui.ui_main import MainWindow
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Close splash screen
    if splash:
        splash.finish(window)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()