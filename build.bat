@echo off
SETLOCAL EnableDelayedExpansion

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
    echo Please install Python 3.10 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [INFO] Python found: 
python --version
echo.

REM Check if logo file exists
if not exist "images\logo.ico" (
    echo [WARNING] Logo file not found at images\logo.ico
    echo The executable will be built without an icon.
    echo.
    set ICON_OPTION=
) else (
    echo [INFO] Logo file found: images\logo.ico
    set ICON_OPTION=--icon=images\logo.ico
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo [INFO] Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created successfully.
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

if !force_deps! == 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (

        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
)

if !force_deps! == 1 (
    echo [INFO] Installing/Verifying PyInstaller 5.x, tinyaes, and compatible NumPy...
    pip install "pyinstaller<6.0" tinyaes "numpy<2.0.0"
) else (
    echo [INFO] Skipping dependency installation. Use --force-deps to install.
)

if !clean! == 1 (
    echo [INFO] Cleaning previous builds...
    if exist "build\" rmdir /s /q build
    if exist "dist\" rmdir /s /q dist
    if exist "*.spec" del /q *.spec
) else (
    echo [INFO] Skipping clean. Use --clean to force a clean build.
)
echo ===============================================
echo   Building PlanIFlow - ProjectPlanner
echo ===============================================
echo.

set spec_file=PlanIFlow_1.7.exe.spec

echo [INFO] Generating spec file...
set makespec_command=pyi-makespec --windowed --name="PlanIFlow_1.7.exe" ^
    %ICON_OPTION% ^
    --version-file=version_info.txt ^
    --add-data="images;images" ^
    --add-data="calendar_manager;calendar_manager" ^
    --add-data="constants;constants" ^
    --add-data="data_manager;data_manager" ^
    --add-data="exporter;exporter" ^
    --add-data="settings_manager;settings_manager" ^
    --add-data="ui;ui" ^
    --hidden-import=PyQt6 ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=matplotlib ^
    --hidden-import=matplotlib.backends.backend_qtagg ^
    --hidden-import=matplotlib.patches ^
    --hidden-import=pandas ^
    --hidden-import=openpyxl ^
    --hidden-import=openpyxl.styles ^
    --hidden-import=reportlab ^
    --hidden-import=reportlab.platypus ^
    --hidden-import=PIL ^
    --hidden-import=reportlab.lib ^
    --hidden-import=reportlab.platypus.tableofcontents ^
    --collect-all PyQt6 ^
    --collect-all matplotlib ^
    --noconsole ^
    --noupx

if !onedir! == 1 (
    set makespec_command=!makespec_command! --onedir
) else (
    set makespec_command=!makespec_command! --onefile
)

!makespec_command! main.py

echo [INFO] Modifying spec file to increase recursion limit...
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
echo [SUCCESS] Executable created: dist\PlanIFlow_1.7.exe
echo [INFO] Icon has been embedded in the executable
echo.

REM Display file info
for %%A in ("dist\PlanIFlow_1.7.exe") do (
    set size=%%~zA
    set /a sizeMB=!size! / 1048576
    echo [INFO] File size: !sizeMB! MB
)
echo.
echo   Build process complete!
echo ===============================================
pause
