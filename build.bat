@echo off
setlocal

echo Building prompt-tuner...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: python is not installed
    exit /b 1
)

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -e ".[dev]"
if %errorlevel% neq 0 exit /b 1

echo Running tests...
python -m pytest tests/ -v
if %errorlevel% neq 0 exit /b 1

echo.
echo Build successful!
echo.
echo Usage:
echo   .venv\Scripts\activate.bat
echo   prompt-tuner run examples\summarize.yaml
