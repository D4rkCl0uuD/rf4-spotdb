@echo off
cd /d "%~dp0"
rem Nutzt die PyCharm-Umgebung (.venv) im übergeordneten Ordner, falls vorhanden
if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" main.py
) else (
    python main.py
)
if errorlevel 1 pause
