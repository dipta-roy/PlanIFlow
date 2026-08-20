@echo off
echo =========================================
echo PlanIFlow Code Quality ^& Security Scan
echo =========================================

echo.
echo Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] venv\Scripts\activate.bat not found! Scans will run in current Python environment.
)

echo.
echo 1/7 Running Ruff Linter ^& Formatter...
where ruff >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    ruff check --fix . > ruff_report.txt
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Ruff passed!
    ) else (
        echo [!] Ruff found issues. See ruff_report.txt
    )
) else (
    echo [SKIP] Ruff not installed.
)

echo.
echo 2/7 Running MyPy Static Type Check...
where mypy >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    mypy . > mypy_report.txt
    if %ERRORLEVEL% EQU 0 (
        echo [OK] MyPy passed!
    ) else (
        echo [!] MyPy found issues. See mypy_report.txt
    )
) else (
    echo [SKIP] MyPy not installed.
)

echo.
echo 3/7 Running Bandit Security Scan...
where bandit >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    bandit -r . -ll -x .\tests,.\dist,.\build,.\venv > bandit_report.txt 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Bandit passed!
    ) else (
        echo [!] Bandit found issues. See bandit_report.txt
    )
) else (
    echo [SKIP] Bandit not installed.
)

echo.
echo 4/7 Running pip-audit Dependency Vulnerability Scan...
where pip-audit >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    pip-audit > pip_audit_report.txt 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] pip-audit passed!
    ) else (
        echo [!] pip-audit found vulnerability issues. See pip_audit_report.txt
    )
) else (
    echo [SKIP] pip-audit not installed. (Install with: pip install pip-audit)
)

echo.
echo 5/7 Running Vulture Dead Code Analysis...
where vulture >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    vulture . --min-confidence 80 --exclude venv,build,dist > vulture_report.txt 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Vulture passed! No dead code detected.
    ) else (
        echo [!] Vulture found dead code candidates. See vulture_report.txt
    )
) else (
    echo [SKIP] Vulture not installed. (Install with: pip install vulture)
)

echo.
echo 6/7 Running Xenon Code Complexity Check...
where xenon >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    xenon --max-absolute C --max-modules C --max-average B --ignore "venv,build,dist,tests" . > xenon_report.txt 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Xenon complexity check passed!
    ) else (
        echo [!] Xenon detected code exceeding complexity thresholds. See xenon_report.txt
    )
) else (
    echo [SKIP] Xenon not installed. (Install with: pip install xenon)
)

echo.
echo 7/7 Running Gitleaks Secret Scan...
where gitleaks >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    gitleaks detect --no-git --report-path gitleaks_report.txt >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Gitleaks passed! No secrets found.
    ) else (
        echo [!] Gitleaks found potential secrets. See gitleaks_report.txt
    )
) else (
    echo [SKIP] Gitleaks not installed on PATH.
)

echo.
echo =========================================
echo All scans complete! Generated reports:
echo - ruff_report.txt
echo - mypy_report.txt
echo - bandit_report.txt
echo - pip_audit_report.txt
echo - vulture_report.txt
echo - xenon_report.txt
echo - gitleaks_report.txt
echo =========================================
pause
