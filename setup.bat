@echo off
REM ============================================================
REM  AI Employee — One-Time Setup Script (Windows)
REM  Bronze Tier
REM ============================================================
REM  Run this ONCE before first use.
REM  What it does:
REM    1. Checks Python version
REM    2. Installs dependencies
REM    3. Creates .env from .env.example
REM    4. Verifies vault structure
REM    5. Runs a DRY_RUN agent pass to verify installation
REM ============================================================

cd /d "%~dp0"
echo.
echo ============================================================
echo   AI Employee — Bronze Tier Setup
echo ============================================================
echo.

REM ── Step 1: Check Python ─────────────────────────────────────
echo [1/5] Checking Python version...
python --version 2>NUL
IF ERRORLEVEL 1 (
    echo [ERROR] Python not found. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
echo       OK
echo.

REM ── Step 2: Install dependencies ────────────────────────────
echo [2/5] Installing dependencies...
pip install -r requirements.txt
IF ERRORLEVEL 1 (
    echo [ERROR] pip install failed. Check internet connection and try again.
    pause
    exit /b 1
)
echo       OK
echo.

REM ── Step 3: Create .env ──────────────────────────────────────
echo [3/5] Creating .env file...
IF NOT EXIST ".env" (
    copy ".env.example" ".env" >NUL
    echo       Created .env from .env.example
    echo       Edit .env to configure if needed.
) ELSE (
    echo       .env already exists — skipping.
)
echo.

REM ── Step 4: Verify vault structure ──────────────────────────
echo [4/5] Verifying vault structure...
python -c "
from pathlib import Path
dirs = [
    'AI_Employee_Vault/Inbox',
    'AI_Employee_Vault/Needs_Action',
    'AI_Employee_Vault/Done',
    'AI_Employee_Vault/Plans',
    'AI_Employee_Vault/Pending_Approval',
    'AI_Employee_Vault/Approved',
    'AI_Employee_Vault/Rejected',
    'AI_Employee_Vault/Logs',
    'AI_Employee_Vault/Skills',
]
for d in dirs:
    p = Path(d)
    p.mkdir(parents=True, exist_ok=True)
    print(f'  OK: {d}')
"
echo.

REM ── Step 5: Dry-run verification ────────────────────────────
echo [5/5] Running DRY_RUN verification pass...
set DRY_RUN=true
python claude_agent.py --update-dashboard
IF ERRORLEVEL 1 (
    echo [ERROR] Agent dry-run failed. Check logs.
    pause
    exit /b 1
)
echo       Dashboard.md generated successfully.
echo.

echo ============================================================
echo   Setup Complete!
echo ============================================================
echo.
echo   Next steps:
echo     1. Start watcher:  run_watcher.bat
echo     2. Drop a file into AI_Employee_Vault\Inbox\
echo     3. Run agent:      run_agent.bat
echo     4. Check results:  AI_Employee_Vault\Dashboard.md
echo.
echo   Test with dry-run first:
echo     run_watcher.bat --dry
echo     run_agent.bat --dry
echo.
pause
