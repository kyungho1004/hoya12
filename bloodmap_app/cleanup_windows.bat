@echo off
REM cleanup_windows.bat — double-click friendly cleaner for Windows
REM Run from the folder where app.py is located.
setlocal ENABLEDELAYEDEXPANSION

REM Try Python via py launcher first, then python, then python3
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 clean_now.py
  goto :end
)
where python >nul 2>&1
if %errorlevel%==0 (
  python clean_now.py
  goto :end
)
where python3 >nul 2>&1
if %errorlevel%==0 (
  python3 clean_now.py
  goto :end
)

echo [ERROR] Python not found. Please install Python 3.x and try again.
pause
:end
