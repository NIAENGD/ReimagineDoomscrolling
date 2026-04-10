@echo off
setlocal
set ROOT=%~dp0
set VENV=%ROOT%.venv

:menu
echo ReimagineDoomscrolling - Full Stack Manager
echo 1. Bootstrap all dependencies (Python + Node)
echo 2. Run backend API
echo 3. Run frontend UI
echo 4. Run both backend and frontend
echo 5. Run test suite
echo 6. Open development plan manager
echo 7. Exit
set /p choice="Select option [1-7]: "

if "%choice%"=="1" goto bootstrap
if "%choice%"=="2" goto backend
if "%choice%"=="3" goto frontend
if "%choice%"=="4" goto both
if "%choice%"=="5" goto tests
if "%choice%"=="6" goto plan
if "%choice%"=="7" goto end

goto menu

:bootstrap
if not exist "%VENV%" python -m venv "%VENV%"
call "%VENV%\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r "%ROOT%requirements.txt"
cd /d "%ROOT%frontend"
if not exist node_modules npm install
cd /d "%ROOT%"
echo Bootstrap complete.
pause
goto menu

:backend
call "%VENV%\Scripts\activate.bat"
python "%ROOT%server.py"
goto end

:frontend
cd /d "%ROOT%frontend"
npm run dev
goto end

:both
start "Backend" cmd /k "call %VENV%\Scripts\activate.bat && python %ROOT%server.py"
start "Frontend" cmd /k "cd /d %ROOT%frontend && npm run dev"
goto end

:plan
call "%ROOT%manage_dev_plan.bat"
goto menu

:tests
call "%VENV%\Scripts\activate.bat"
pytest backend/tests -q
cd /d "%ROOT%frontend"
npm test
cd /d "%ROOT%"
pause
goto menu

:end
endlocal
