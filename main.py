"""
PlanIFlow - Project Planner - Main Entry Point
A desktop project management application similar to Microsoft Project
"""

import sys
import os
import base64

# Import only essential PyQt6 modules first for fast splash screen

import traceback
from PyQt6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt
from constants.constants import (
    APP_NAME, VERSION, ERROR_TITLE, ERROR_GENERIC_MESSAGE
)
from data_manager.temp_manager import TempFileManager


def handle_exception(type, value, tb):
    """Global exception handler to prevent app crash and show popup"""
    # Print the full traceback to stderr for debugging
    error_msg = "".join(traceback.format_exception(type, value, tb))
    print(error_msg, file=sys.stderr)

    # Show a generic error popup to the user
    if QApplication.instance():
        try:
            # We use the generic message from constants
            QMessageBox.critical(
                None,
                ERROR_TITLE,
                f"{ERROR_GENERIC_MESSAGE}\n\nError: {str(value)}",
                QMessageBox.StandardButton.Ok
            )
        except Exception as e:
            # Last resort if message box fails
            print(f"Failed to show error message box: {e}", file=sys.stderr)


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
    try:
        _main_impl()
    except Exception:
        # Emergency logging for startup crashes
        error_msg = traceback.format_exc()
        try:
            log_path = os.path.join(os.path.expanduser("~"), "PlanIFlow_Startup_Error.log")
            with open(log_path, "w") as f:
                f.write(error_msg)
            # Try to show message box if Qt is alive
            if QApplication.instance():
                QMessageBox.critical(None, "Startup Error", f"An error occurred during startup.\nSee {log_path}\n\n{error_msg}")
        except:
            pass
        sys.exit(1)

def _main_impl():
    # Set global exception hook
    sys.excepthook = handle_exception

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
    # Create icon from base64 ICO data - save to temp file to preserve all icon sizes
    icon_bytes = base64.b64decode(LOGO_ICO_BASE64)
    temp_icon_path = TempFileManager.get_temp_path(suffix='.ico', prefix='app_icon_')
    
    try:
        with open(temp_icon_path, 'wb') as f:
            f.write(icon_bytes)
        
        # Load icon from temp file (preserves all sizes in .ico)
        app_icon = QIcon()
        app_icon.addFile(temp_icon_path)
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)
    except Exception as e:
        print(f"Error setting app icon: {e}")
    # TempFileManager will handle cleanup on application exit
    
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