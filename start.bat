@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv" (
    echo Virtual environment not found. Run build.bat first.
    exit /b 1
)

call .venv\Scripts\activate.bat

if "%~1"=="" (
    echo Usage:
    echo   start.bat run examples\summarize.yaml                # Run a task
    echo   start.bat run examples\summarize.yaml -o report.json # Export JSON
    echo   start.bat run examples\summarize.yaml --no-ai-scoring # Rules only
    echo   start.bat models                                     # List models
    echo.
    prompt-tuner --help
) else (
    prompt-tuner %*
)
