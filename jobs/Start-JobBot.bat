@echo off
title JobBot
cd /d "%~dp0"
echo ============================================
echo   JobBot
echo   Leave this window OPEN while you use it.
echo   Close the window (or press Ctrl+C) to stop.
echo ============================================
echo.
where py >nul 2>nul
if %errorlevel% neq 0 (
  echo Python was not found on this PC.
  echo.
  echo Install Python from https://www.python.org/downloads/
  echo IMPORTANT: during install, tick the box "Add python.exe to PATH".
  echo Then run this file again.
  echo.
  pause
  exit /b 1
)
if not exist ".jobbot-setup-done" (
  echo First run only: installing what JobBot needs.
  echo This can take a few minutes - please wait...
  echo.
  py -m pip install -r requirements.txt
  py -m playwright install chromium
  if exist "..\full-board-export.json" (
    echo.
    echo Bringing in your job board - please wait...
    py -m jobbot import-board "..\full-board-export.json"
  )
  echo done> ".jobbot-setup-done"
  echo.
  echo Setup finished.
  echo.
)
py -m jobbot
pause
