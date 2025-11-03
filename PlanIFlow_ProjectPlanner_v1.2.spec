# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('images', 'images'), ('data_manager.py', '.'), ('calendar_manager.py', '.'), ('gantt_chart.py', '.'), ('exporter.py', '.'), ('themes.py', '.'), ('ui_main.py', '.'), ('settings_manager.py', '.'), ('ui_dashboard.py', '.'), ('ui_menu_toolbar.py', '.'), ('ui_tasks.py', '.'), ('ui_resources.py', '.'), ('ui_project_settings.py', '.'), ('ui_delegates.py', '.'), ('settings_manager_new.py', '.'), ('ui_helpers.py', '.')]
binaries = []
hiddenimports = ['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'matplotlib', 'matplotlib.backends.backend_qtagg', 'matplotlib.patches', 'pandas', 'openpyxl', 'openpyxl.styles']
tmp_ret = collect_all('PyQt6')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('matplotlib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PlanIFlow_ProjectPlanner_v1.2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['images\\logo.ico'],
)
