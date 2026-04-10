@echo off
setlocal EnableDelayedExpansion
set ROOT=%~dp0

:menu
cls
echo ============================================
echo ReimagineDoomscrolling - Dev Plan Manager
echo ============================================
echo 1. Open DevelopmentPlan.md
echo 2. Run backend test quick check
echo 3. Run frontend test quick check
echo 4. Verify key project files
echo 5. Generate timestamped status report
echo 6. Exit
set /p choice="Select option [1-6]: "

if "%choice%"=="1" goto open_plan
if "%choice%"=="2" goto test_backend
if "%choice%"=="3" goto test_frontend
if "%choice%"=="4" goto verify
if "%choice%"=="5" goto report
if "%choice%"=="6" goto end

goto menu

:open_plan
if exist "%ROOT%DevelopmentPlan.md" (
  start "" notepad "%ROOT%DevelopmentPlan.md"
) else (
  echo DevelopmentPlan.md not found.
  pause
)
goto menu

:test_backend
if exist "%ROOT%.venv\Scripts\activate.bat" (
  call "%ROOT%.venv\Scripts\activate.bat"
) else (
  echo Warning: .venv not found. Use run_app.bat option 1 first.
)
pytest "%ROOT%backend\tests" -q
pause
goto menu

:test_frontend
if not exist "%ROOT%frontend\node_modules" (
  echo Warning: frontend dependencies not installed. Use run_app.bat option 1 first.
  pause
  goto menu
)
cd /d "%ROOT%frontend"
npm test
cd /d "%ROOT%"
pause
goto menu

:verify
set ERRORS=0
for %%F in (README.md DevelopmentPlan.md run_app.bat manage_dev_plan.bat server.py requirements.txt) do (
  if exist "%ROOT%%%F" (
    echo [OK] %%F
  ) else (
    echo [MISSING] %%F
    set /a ERRORS+=1
  )
)
if !ERRORS! GTR 0 (
  echo Verification completed with !ERRORS! missing file^(s^).
) else (
  echo Verification completed successfully.
)
pause
goto menu

:report
if not exist "%ROOT%docs\status" mkdir "%ROOT%docs\status"
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%I
set REPORT=%ROOT%docs\status\dev_status_!TS!.md
(
  echo # Development Status Report
  echo.
  echo - Generated: !TS!
  echo - Plan file: DevelopmentPlan.md
  echo - Notes: Update this report with progress against milestones.
) > "!REPORT!"
echo Created !REPORT!
pause
goto menu

:end
endlocal
