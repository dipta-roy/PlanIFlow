"""ui_helpers.py - helper utilities extracted from ui_main.py"""


import sys, os
def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def set_application_icon(window, logo_path):
    """Set application icon for window and QApplication using get_resource_path"""
    try:
        path = get_resource_path(logo_path)
    except Exception:
        path = logo_path
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication
    import os
    if os.path.exists(path):
        icon = QIcon(path)
        window.setWindowIcon(icon)
        app = QApplication.instance()
        if app:
            app.setWindowIcon(icon)
