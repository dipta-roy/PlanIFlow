import sys
import os
from cx_Freeze import setup, Executable
sys.setrecursionlimit(5000)
sys.path.append(os.getcwd())
base = "Win32GUI" if sys.platform == "win32" else None
icon_path = os.path.abspath("images/logo.ico")

# GUID for the application
# This specific UUID allows for future upgrades of the MSI.
# Do NOT change this in future versions of PlaniFlow, or upgrades won't work automatically.
UPGRADE_CODE = "{61A8256E-8095-4683-8472-35C433694038}"

# Build Options
build_exe_options = {
    "packages": [
        "os", "sys", "ctypes", 
        "calendar_manager", "command_manager", "constants", 
        "data_manager", "exporter", "settings_manager", "ui",
        "PyQt6", "pandas", "openpyxl", "matplotlib", "reportlab", 
        "numpy", "PIL", "jsonschema", "dateutil", "referencing", "attrs"
    ],
    # Exclude heavy/unused libraries that might confuse cx_Freeze or cause recursion errors
    "excludes": [
        "tkinter", "unittest", "xmlrpc", "notebook", "ipython",
        "torch", "scipy", "curses", "pydoc", "pygments",
        "PyQt6.QtQml", "PyQt6.QtQuick", "PyQt6.QtSql", "PyQt6.Qt3DCore"
    ],
    # Explicitly ignore missing DLLs that are not needed
    "bin_excludes": [
        "LIBPQ.dll", "OCI.dll", "fbclient.dll", "MIMAPI64.dll",
        "Qt63DQuickScene2D.dll", "Qt63DQuickScene3D.dll", 
        "Qt6QmlCompiler.dll", "Qt6QmlCore.dll", "Qt6QmlLocalStorage.dll",
        "Qt6QmlNetwork.dll", "Qt6QmlXmlListModel.dll",
        "Qt6Quick3DParticleEffects.dll", 
        "Qt6QuickControls2FluentWinUI3StyleImpl.dll",
        "Qt6QuickControls2WindowsStyleImpl.dll",
        "Qt6QuickShapesDesignHelpers.dll",
        "Qt6QuickVectorImageHelpers.dll"
    ],
    "include_files": [
        (icon_path, "images/logo.ico"),
        ("images/Logo.png", "images/Logo.png"),
        ("images/logo_lg.ico", "images/logo_lg.ico"),
        ("data_manager/project_schema.json", "data_manager/project_schema.json"),
        ("sample/", "sample/"), # Include sample data if needed
    ],
    "include_msvcr": True,  # Include Microsoft Visual C++ Redistributable
    # "zip_include_packages": ["*"],  # Optimization: Zip all packages
    # "zip_exclude_packages": [],
    "optimize": 2,  # Optimize bytecode
}

# MSI Options
bdist_msi_options = {
    "add_to_path": True,
    "upgrade_code": UPGRADE_CODE,
    "initial_target_dir": r"[ProgramFilesFolder]\PlaniFlow",
    "install_icon": icon_path,
    "target_name": "PlanIFlow_Setup_2.4.0.msi",
}

# Executable Configuration
target = Executable(
    script="main.py",
    base=base,
    target_name="PlanIFlow.exe",
    icon=icon_path,
    shortcut_name="PlanIFlow",
    shortcut_dir="DesktopFolder",  # Create shortcut on Desktop
)

setup(
    name="PlanIFlow",
    version="2.4.0",
    description="PlanIFlow Project Planner",
    author="Dipta Roy",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=[target],
)
