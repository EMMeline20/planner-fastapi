@echo off
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8090" ^| findstr "LISTENING"') do (
  echo Stopping PID %%a
  taskkill /PID %%a /F >nul 2>&1
)
