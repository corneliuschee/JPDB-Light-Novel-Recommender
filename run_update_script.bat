@echo off
set "logfile=%TEMP%\daily_jpdb_run.txt"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "today=%%i"
if exist "%logfile%" (
    set /p lastRun=<"%logfile%"
    if "%lastRun%"=="%today%" (
        echo Already ran today. Exiting.
        exit /b
    )
)
echo %today% > "%logfile%"
start C:\Users\Admin\AppData\Local\Programs\Anki\anki.exe
timeout /t 10 /nobreak
cd "C:\Users\Admin\OneDrive\Documents\Coding Projects\JPDB Project"
call ".venv\Scripts\activate.bat"
python update_db_script.py
taskkill /IM anki.exe /F
