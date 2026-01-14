"""ui_helpers.py - helper utilities extracted from ui_main.py"""

import sys, os
import base64
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication
from constants.app_images import LOGO_ICO_BASE64

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def set_application_icon(window, logo_base64=None):
    """Set application icon for window and QApplication using base64 encoded icon"""
    if logo_base64 is None:
        # Import from app_images if not provided
        logo_base64 = LOGO_ICO_BASE64
    
    try:
        icon_bytes = base64.b64decode(logo_base64)
        icon_pix = QPixmap()
        icon_pix.loadFromData(icon_bytes)
        
        if not icon_pix.isNull():
            icon = QIcon(icon_pix)
            window.setWindowIcon(icon)
            app = QApplication.instance()
            if app:
                app.setWindowIcon(icon)
    except Exception as e:
        print(f"Error setting application icon: {e}")
