@echo off
SETLOCAL EnableDelayedExpansion

set spec_file=PlanIFlow_2.2.0.exe.spec

set force_deps=0
set encrypt=0
set onedir=0
set clean=0

:arg_loop
if "%~1"=="" goto arg_loop_end
if "%~1"=="--force-deps" set force_deps=1
if "%~1"=="--encrypt" set encrypt=1
if "%~1"=="--onedir" set onedir=1
if "%~1"=="--clean" set clean=1
shift
goto arg_loop

:arg_loop_end

echo ===============================================
echo   PlanIFlow - Project Planner - Build to EXE
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo [INFO] Python found:
python --version
echo.

REM Check if logo file exists
if not exist "images\logo.ico" (
    echo [WARNING] Logo file not found at images\logo.ico
    set ICON_OPTION=
) else (
    echo [INFO] Logo file found: images\logo.ico
    set ICON_OPTION=--icon=images\logo.ico
)

REM Check if virtual environment exists and create if needed
if not exist "venv\" (
    echo [INFO] Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created successfully.
    set force_deps=1
    echo [INFO] Forcing dependency install after venv creation.
    echo.
) else (
    echo [INFO] Virtual environment already exists.
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)
echo.

REM Install dependencies if forced or if venv was just created
if !force_deps! == 1 (
    echo [INFO] Installing/Verifying PyInstaller and project dependencies from requirements.txt...
    pip install -r requirements.txt
    pip install "pyinstaller<6.0" tinyaes
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed successfully.
) else (
    echo [INFO] Skipping dependency installation. Use --force-deps to install/verify.
)

if !clean! == 1 (
    echo [INFO] Cleaning previous builds...
    if exist "build\" rmdir /s /q build
    if exist "dist\" rmdir /s /q dist
    if exist "!spec_file!" del /q "!spec_file!"
) else (
    echo [INFO] Skipping clean. Use --clean to force a clean build.
)
echo ===============================================
echo   Building PlanIFlow - ProjectPlanner
echo ===============================================
echo.


echo [INFO] Generating spec file for final Windowed release...
set makespec_command=pyi-makespec --windowed --name="PlanIFlow_2.2.0.exe" ^
%ICON_OPTION% ^
--version-file=version_info.txt ^
--add-data="images;images" ^
--add-data="calendar_manager;calendar_manager" ^
--add-data="constants;constants" ^
--add-data="command_manager;command_manager" ^
--add-data="data_manager;data_manager" ^
--add-data="exporter;exporter" ^
--add-data="settings_manager;settings_manager" ^
--add-data="ui;ui" ^
--hidden-import=PyQt6.QtWidgets ^
--hidden-import=PyQt6.QtGui ^
--hidden-import=PyQt6.QtCore ^
--hidden-import=reportlab ^
--hidden-import=reportlab.pdfgen ^
--hidden-import=reportlab.platypus ^
--hidden-import=reportlab.lib ^
--hidden-import=reportlab.platypus.tableofcontents ^
--hidden-import=matplotlib.pyplot ^
--hidden-import=matplotlib.patches ^
--hidden-import=matplotlib.dates ^
--hidden-import=matplotlib.figure ^
--hidden-import=matplotlib.backends.backend_qtagg ^
--hidden-import=pandas ^
--hidden-import=numpy ^
--hidden-import=Pillow ^
--hidden-import=openpyxl ^
--hidden-import=openpyxl.styles ^
--collect-all PyQt6 ^
--collect-all matplotlib ^
--collect-all numpy ^
--noconsole ^
--noupx

if !onedir! == 1 (
    set makespec_command=!makespec_command! --onedir
) else (
    set makespec_command=!makespec_command! --onefile
)


:: 1. CREATE THE SPEC FILE FIRST
echo [INFO] Running makespec command...
!makespec_command! main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to generate spec file!
    pause
    exit /b 1
)


:: 2. THEN MODIFY THE SPEC FILE
echo [INFO] Modifying spec file to set fixed recursion limit...
python prepare_spec.py "!spec_file!"


set build_command=pyinstaller --noconfirm "!spec_file!"

if !encrypt! == 1 (
    echo [INFO] Encryption enabled.
    set build_command=!build_command! --key="PfV2_SecKey_9x82"
) else (
    echo [INFO] Encryption disabled.
)

echo [INFO] Running build command: !build_command!
!build_command!

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   Build completed successfully!
echo ===============================================
echo.
echo [SUCCESS] Executable created: dist\PlanIFlow_2.2.0.exe
REM Display file info
for %%A in ("dist\PlanIFlow_2.2.0.exe") do (
    set size=%%~zA
    set /a sizeMB=!size! / 1048576
    echo [INFO] File size: !sizeMB! MB
)
echo.
echo   Run the EXE and share the traceback error.
echo ===============================================
pause