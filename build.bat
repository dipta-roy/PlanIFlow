@echo off
:: Enable delayed expansion to allow for variable access within loops using !var! syntax.
SETLOCAL EnableDelayedExpansion

:: =================================================================================
:: Default Settings & Script Configuration
:: =================================================================================
:: Define the name of the PyInstaller spec file to be generated.
set spec_file=PlanIFlow_2.0.0.exe.spec

:: Default build flags. These can be overridden by command-line arguments.
set force_deps=1 :: 1 = Always install/update dependencies. 0 = Skip.
set encrypt=0    :: 1 = Encrypt the executable. 0 = Do not encrypt.
set onedir=0     :: 1 = Build a one-folder bundle. 0 = Build a single executable file.
set clean=1      :: 1 = Clean previous build artifacts before starting. 0 = Skip cleaning.

:: =================================================================================
:: Argument Parsing Loop
:: =================================================================================
:: This loop parses command-line arguments and updates the build flags accordingly.
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

:: =================================================================================
:: Environment Validation
:: =================================================================================
:: Check if Python is installed and available in the system's PATH.
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b 1
)
echo [INFO] Python found:
python --version
echo.

:: Check if the application icon file exists.
if not exist "images\logo.ico" (
    echo [WARNING] Logo file not found at images\logo.ico
    set ICON_OPTION=
) else (
    echo [INFO] Logo file found: images\logo.ico
    set ICON_OPTION=--icon=images\logo.ico
)

:: =================================================================================
:: Virtual Environment Setup
:: =================================================================================
:: Check if a virtual environment directory already exists.
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

:: Activate the virtual environment. 'call' is used to run the batch script in the same context.
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)
echo.

:: =================================================================================
:: Dependency Installation
:: =================================================================================
:: If force_deps is enabled, install all required packages.
if !force_deps! == 1 (
    echo [INFO] Installing/Verifying Dependencies from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies from requirements.txt!
        pause
        exit /b 1
    )
	
	:: Install build-specific tools that are not needed for running the app directly.
    echo [INFO] Installing build tools (PyInstaller, tinyaes)...
    pip install "pyinstaller<6.0" tinyaes
) else (
    echo [INFO] Skipping dependency installation. Use --force-deps to force installation.
)

:: =================================================================================
:: Pre-Build Cleaning
:: =================================================================================
:: If clean is enabled, remove directories and files from previous builds.
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

:: =================================================================================
:: 1. Generate PyInstaller Spec File
:: =================================================================================
echo [INFO] Generating spec file for final Windowed release...
:: This command constructs the command to generate the .spec file.
:: It includes many flags to tell PyInstaller how to bundle the application.
set makespec_command=pyi-makespec --windowed --name="PlanIFlow_2.0.0.exe" ^
%ICON_OPTION% ^
--version-file=version_info.txt ^
:: --add-data: Bundles directories into the final executable.
--add-data="images;images" ^
--add-data="calendar_manager;calendar_manager" ^
--add-data="constants;constants" ^
--add-data="data_manager;data_manager" ^
--add-data="exporter;exporter" ^
--add-data="settings_manager;settings_manager" ^
--add-data="ui;ui" ^
:: --hidden-import: Tells PyInstaller about modules that are not automatically detected.
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
:: --collect-all: Gathers all submodules, data files, and binaries from a package.
--collect-all PyQt6 ^
--collect-all matplotlib ^
--collect-all numpy ^
:: --noconsole: Creates a windowed application without a console window.
--noconsole ^
:: --noupx: Disables UPX compression, which can sometimes cause issues with antivirus software.
--noupx

:: Append --onedir or --onefile based on the script's flag.
if !onedir! == 1 (
    set makespec_command=!makespec_command! --onedir
) else (
    set makespec_command=!makespec_command! --onefile
)

:: Execute the makespec command to create the initial spec file.
echo [INFO] Running makespec command...
!makespec_command! main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to generate spec file!
    pause
    exit /b 1
)

:: =================================================================================
:: 2. Modify the Spec File
:: =================================================================================
:: Run a Python script to perform advanced modifications to the .spec file.
:: This is used for settings that pyi-makespec does not support directly.
echo [INFO] Modifying spec file to set fixed recursion limit...
python prepare_spec.py "!spec_file!"

:: =================================================================================
:: 3. Build the Executable
:: =================================================================================
:: Base command for the final build process.
set build_command=pyinstaller --noconfirm "!spec_file!"

:: If encryption is enabled, add the encryption key.
if !encrypt! == 1 (
    echo [INFO] Encryption enabled.
    set build_command=!build_command! --key="PfV2_SecKey_9x82"
) else (
    echo [INFO] Encryption disabled.
)

:: Execute the final build command.
echo [INFO] Running build command: !build_command!
!build_command!

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

:: =================================================================================
:: 4. Post-Build Summary
:: =================================================================================
echo.
echo ===============================================
echo   Build completed successfully!
echo ===============================================
echo.
echo [SUCCESS] Executable created: dist\PlanIFlow_2.0.0.exe

:: Display the final size of the executable.
for %%A in ("dist\PlanIFlow_2.0.0.exe") do (
    set size=%%~zA
    set /a sizeMB=!size! / 1048576
    echo [INFO] File size: !sizeMB! MB
)
echo.
echo   BUILDING WITH CONSOLE ENABLED FOR DEBUGGING!
echo   Run the EXE and share the traceback error.
echo ===============================================
pause