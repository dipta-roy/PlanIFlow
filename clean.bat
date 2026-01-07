@echo off
SETLOCAL EnableDelayedExpansion

echo ===============================================
echo   PlanIFlow - Clean Build Files
echo ===============================================
echo.

set /p CONFIRM="This will remove build artifacts (build/, dist/), cache files, and temporary installer files. Continue? (Y/N): "
if /i not "!CONFIRM!"=="Y" (
    echo [INFO] Cleanup cancelled.
    pause
    exit /b 0
)

echo.
echo [INFO] Cleaning build artifacts...
echo.

set FILES_CLEANED=0

:: Remove build folder (cx_Freeze / PyInstaller)
if exist "build\" (
    rmdir /s /q build
    echo [SUCCESS] Removed build\ folder.
    set /a FILES_CLEANED+=1
)

:: Remove dist folder (MSI / EXE output)
if exist "dist\" (
    rmdir /s /q dist
    echo [SUCCESS] Removed dist\ folder.
    set /a FILES_CLEANED+=1
)

:: Remove spec files
if exist "*.spec" (
    del /q *.spec
    echo [SUCCESS] Removed root .spec files.
    set /a FILES_CLEANED+=1
)
if exist "installer\*.spec" (
    del /q "installer\*.spec"
    echo [SUCCESS] Removed installer .spec files.
    set /a FILES_CLEANED+=1
)

:: Remove temporary installer artifacts
if exist "installer\payload.zip" (
    del /q "installer\payload.zip"
    echo [SUCCESS] Removed installer\payload.zip.
    set /a FILES_CLEANED+=1
)
if exist "installer\setup_icon.ico" (
    del /q "installer\setup_icon.ico"
    echo [SUCCESS] Removed installer\setup_icon.ico.
    set /a FILES_CLEANED+=1
)

:: Remove __pycache__ folders recursively
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    rmdir /s /q "%%d"
    echo [INFO] Removed %%d
    set /a FILES_CLEANED+=1
)

:: Remove .pyc files recursively
for /r . %%f in (*.pyc) do @if exist "%%f" (
    del /q "%%f"
    set /a FILES_CLEANED+=1
)

:: Remove application cache/state files
if exist ".last_project" (
    del /q .last_project
    echo [SUCCESS] Removed .last_project cache.
    set /a FILES_CLEANED+=1
)

echo.
if !FILES_CLEANED! gtr 0 (
    echo [SUCCESS] Cleanup completed! Removed !FILES_CLEANED! items/folders.
) else (
    echo [INFO] Nothing to clean - project is already clean.
)
echo.

set /p CLEAN_VENV="Do you also want to remove the virtual environment (venv/)? (Y/N): "
if /i "!CLEAN_VENV!"=="Y" (
    if exist "venv\" (
        echo [INFO] Removing virtual environment...
        rmdir /s /q venv
        echo [SUCCESS] Virtual environment removed.
    ) else (
        echo [INFO] No virtual environment found.
    )
)

echo.
echo ===============================================
echo   Cleanup complete!
echo ===============================================
pause
