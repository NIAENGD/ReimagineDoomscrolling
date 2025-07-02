@echo off
setlocal

:menu
echo ReimagineDoomscrolling Helper

echo 1. Install Python requirements

echo 2. Start local server

echo 3. Start server and open browser

echo 4. Exit
set /p choice="Select option [1-4]: "
if "%choice%"=="1" (
    pip install -r requirements.txt
    pause
    goto menu
)
if "%choice%"=="2" (
    python "%~dp0server.py" %*
    goto end
)
if "%choice%"=="3" (
    start "" http://localhost:5001
    python "%~dp0server.py" %*
    goto end
)
if "%choice%"=="4" goto end

echo Invalid option
pause
goto menu

:end
endlocal
