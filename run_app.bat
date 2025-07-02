@echo off
setlocal
set EXT_DIR=%~dp0extension

:menu
echo ReimagineDoomscrolling Helper

echo 1. Install Python requirements
echo 2. Uninstall Python requirements
echo 3. Start local server
echo 4. Start server and open browser
echo 5. Open extension folder
echo 6. Update from GitHub
echo 7. Exit
set /p choice="Select option [1-7]: "
if "%choice%"=="1" (
    pip install -r "%~dp0requirements.txt"
    pause
    goto menu
)
if "%choice%"=="2" (
    pip uninstall -y -r "%~dp0requirements.txt"
    pause
    goto menu
)
if "%choice%"=="3" (
    python "%~dp0server.py" %*
    goto end
)
if "%choice%"=="4" (
    start "" http://localhost:5001
    python "%~dp0server.py" %*
    goto end
)
if "%choice%"=="5" (
    start "" "%EXT_DIR%"
    goto menu
)
if "%choice%"=="6" (
    git -C "%~dp0" pull
    pause
    goto menu
)
if "%choice%"=="7" goto end

echo Invalid option
pause
goto menu

:end
endlocal
